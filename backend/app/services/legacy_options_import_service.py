import configparser
import os
from pathlib import Path
from io import StringIO

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSetting, BarcodeCounter

DEFAULT_LEGACY_OPTIONS_PATH = r"C:\QazPost\BarCodes new\options.ini"
LEGACY_OPTIONS_ENV_VAR = "LEGACY_OPTIONS_PATH"
LEGACY_OPTIONS_ENCODINGS = ("utf-8-sig", "cp1251", "utf-8")

OPTIONAL_SETTING_MAPPINGS = {
    ("MainSettings", "PagesQuant"): "pages_quant",
    ("MainSettings", "BarCodeScale"): "barcode_scale",
    ("Font", "FontBig"): "font_big",
    ("Font", "FontCenter"): "font_center",
    ("Font", "FontRight"): "font_right",
    ("Font", "Space"): "space",
}


def resolve_legacy_options_path() -> str:
    return os.getenv(LEGACY_OPTIONS_ENV_VAR, DEFAULT_LEGACY_OPTIONS_PATH)


def load_legacy_options(path: str | Path) -> configparser.ConfigParser:
    resolved_path = Path(path)
    if not resolved_path.exists():
        raise ValueError(f"Legacy options.ini file was not found: {resolved_path}")

    file_text: str | None = None
    for encoding in LEGACY_OPTIONS_ENCODINGS:
        try:
            file_text = resolved_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if file_text is None:
        raise ValueError(
            f"Legacy options.ini file could not be decoded with supported encodings: {resolved_path}"
        )

    section_start = file_text.find("[MainSettings]")
    if section_start == -1:
        raise ValueError("Legacy options.ini does not contain the [MainSettings] section.")

    config = configparser.ConfigParser()
    config.optionxform = str
    config.read_file(StringIO(file_text[section_start:]), source=str(resolved_path))

    if not config.has_section("MainSettings"):
        raise ValueError("Legacy options.ini does not contain the MainSettings section.")

    return config


async def upsert_app_setting(
    session: AsyncSession,
    key: str,
    value: str,
) -> str:
    result = await session.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()

    if setting is None:
        session.add(AppSetting(key=key, value=value))
        return "created"

    if setting.value == value:
        return "skipped"

    setting.value = value
    return "updated"


async def import_legacy_options(
    session: AsyncSession,
    options_path: str | Path,
) -> dict[str, int | str]:
    config = load_legacy_options(options_path)
    main_settings = config["MainSettings"]

    if "oblCode" not in main_settings:
        raise ValueError("Legacy options.ini does not contain MainSettings.oblCode.")

    created_counters = 0
    updated_counters = 0
    skipped_counters = 0
    created_settings = 0
    updated_settings = 0
    skipped_settings = 0

    raw_region_code = main_settings["oblCode"].strip()
    region_code = raw_region_code if len(raw_region_code) == 2 and raw_region_code.isdigit() else "01"

    async with session.begin():
        obl_code_status = await upsert_app_setting(
            session=session,
            key="obl_code",
            value=region_code,
        )
        if obl_code_status == "created":
            created_settings += 1
        elif obl_code_status == "updated":
            updated_settings += 1
        else:
            skipped_settings += 1

        for (section_name, option_name), setting_key in OPTIONAL_SETTING_MAPPINGS.items():
            if not config.has_section(section_name) or option_name not in config[section_name]:
                continue

            status = await upsert_app_setting(
                session=session,
                key=setting_key,
                value=config[section_name][option_name].strip(),
            )
            if status == "created":
                created_settings += 1
            elif status == "updated":
                updated_settings += 1
            else:
                skipped_settings += 1

        for option_name, raw_value in main_settings.items():
            if not option_name.startswith("LastBarCodeNumber"):
                continue

            package_type = option_name[-2:].upper()
            if len(package_type) != 2 or not package_type.isalpha():
                skipped_counters += 1
                continue

            try:
                current_value = int(raw_value.strip())
            except ValueError:
                skipped_counters += 1
                continue

            result = await session.execute(
                select(BarcodeCounter)
                .where(BarcodeCounter.package_type == package_type)
                .where(BarcodeCounter.region_code == region_code)
            )
            counter = result.scalar_one_or_none()

            if counter is None:
                session.add(
                    BarcodeCounter(
                        package_type=package_type,
                        region_code=region_code,
                        current_value=current_value,
                    )
                )
                created_counters += 1
                continue

            if counter.current_value == current_value:
                skipped_counters += 1
                continue

            counter.current_value = current_value
            updated_counters += 1

    return {
        "options_path": str(Path(options_path)),
        "created_counters": created_counters,
        "updated_counters": updated_counters,
        "skipped_counters": skipped_counters,
        "created_settings": created_settings,
        "updated_settings": updated_settings,
        "skipped_settings": skipped_settings,
    }
