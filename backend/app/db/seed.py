import asyncio

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models import AppSetting, BarcodeCodeCatalog, BarcodeCounter

DEFAULT_PACKAGE_TYPES = [
    "VC",
    "KG",
    "ON",
    "AD",
    "BP",
    "CE",
    "GF",
    "RZ",
    "AV",
    "UP",
    "CP",
    "CZ",
    "RC",
    "CC",
    "VR",
    "CV",
    "MM",
    "UB",
    "PP",
    "DQ",
    "UE",
    "UO",
    "CF",
    "RW",
    "RG",
    "LR",
    "GP",
    "CO",
    "GB",
    "RR",
]

DEFAULT_SETTINGS = {
    "label_width": "126",
    "label_height": "71",
    "default_rows": "5",
    "default_columns": "2",
    "default_left_margin": "10",
    "default_top_margin": "10",
    "barcode_scale": "1.0",
    "obl_code": "01",
    "country_suffix": "KZ",
    "legacy_dbf_path": r"C:\QazPost\BarCodes new\Dbf_win.dbf",
}


async def seed_barcode_counters() -> tuple[int, int]:
    created_count = 0
    skipped_count = 0
    region_code = DEFAULT_SETTINGS["obl_code"]

    async with AsyncSessionLocal() as session:
        for package_type in DEFAULT_PACKAGE_TYPES:
            result = await session.execute(
                select(BarcodeCounter)
                .where(BarcodeCounter.package_type == package_type)
                .where(BarcodeCounter.region_code == region_code)
            )
            existing_counter = result.scalar_one_or_none()

            if existing_counter is not None:
                skipped_count += 1
                continue

            session.add(
                BarcodeCounter(
                    package_type=package_type,
                    region_code=region_code,
                    current_value=0,
                )
            )
            created_count += 1

        await session.commit()

    return created_count, skipped_count


async def seed_code_catalog() -> tuple[int, int]:
    created_count = 0
    skipped_count = 0

    async with AsyncSessionLocal() as session:
        for package_type in DEFAULT_PACKAGE_TYPES:
            result = await session.execute(
                select(BarcodeCodeCatalog).where(
                    BarcodeCodeCatalog.code == package_type
                )
            )
            existing_entry = result.scalar_one_or_none()

            if existing_entry is not None:
                skipped_count += 1
                continue

            session.add(BarcodeCodeCatalog(code=package_type, status="available"))
            created_count += 1

        await session.commit()

    return created_count, skipped_count


async def seed_app_settings() -> tuple[int, int]:
    created_count = 0
    skipped_count = 0

    async with AsyncSessionLocal() as session:
        for key, value in DEFAULT_SETTINGS.items():
            result = await session.execute(
                select(AppSetting).where(AppSetting.key == key)
            )
            existing_setting = result.scalar_one_or_none()

            if existing_setting is not None:
                skipped_count += 1
                continue

            session.add(AppSetting(key=key, value=value))
            created_count += 1

        await session.commit()

    return created_count, skipped_count


async def seed_database() -> None:
    created_counters, skipped_counters = await seed_barcode_counters()
    created_codes, skipped_codes = await seed_code_catalog()
    created_settings, skipped_settings = await seed_app_settings()

    print(f"Created counters: {created_counters}")
    print(f"Skipped counters: {skipped_counters}")
    print(f"Created catalog codes: {created_codes}")
    print(f"Skipped catalog codes: {skipped_codes}")
    print(f"Created settings: {created_settings}")
    print(f"Skipped settings: {skipped_settings}")


def main() -> None:
    asyncio.run(seed_database())


if __name__ == "__main__":
    main()
