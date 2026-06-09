import re

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSetting, BarcodeCounter

CHECK_DIGIT_WEIGHTS = (8, 6, 4, 2, 3, 5, 9, 7)
PACKAGE_TYPE_PATTERN = re.compile(r"^[A-Z]{2}$")
DEFAULT_OBL_CODE = "01"
DEFAULT_COUNTRY_SUFFIX = "KZ"
MAX_COUNTER_VALUE = 999_999


class CounterNotFoundError(LookupError):
    pass


def validate_package_type(package_type: str) -> str:
    normalized_package_type = package_type.strip().upper()

    if not PACKAGE_TYPE_PATTERN.fullmatch(normalized_package_type):
        raise ValueError("package_type must be exactly 2 uppercase latin letters.")

    return normalized_package_type


def validate_quantity(quantity: int) -> int:
    if quantity < 1 or quantity > 1000:
        raise ValueError("quantity must be between 1 and 1000.")

    return quantity


def calculate_check_digit(body_8_digits: str) -> int:
    if len(body_8_digits) != 8 or not body_8_digits.isdigit():
        raise ValueError("body_8_digits must be an 8-digit string.")

    weighted_sum = sum(
        int(digit) * weight
        for digit, weight in zip(body_8_digits, CHECK_DIGIT_WEIGHTS, strict=True)
    )
    remainder = weighted_sum % 11
    check_digit = 11 - remainder

    if check_digit == 10:
        return 0

    if check_digit == 11:
        return 5

    return check_digit


async def get_setting_value(session: AsyncSession, key: str, default: str) -> str:
    result = await session.execute(select(AppSetting).where(AppSetting.key == key))
    setting = result.scalar_one_or_none()

    if setting is None:
        return default

    normalized_value = setting.value.strip()

    if not normalized_value:
        return default

    return normalized_value


def build_barcode_number(
    package_type: str,
    obl_code: str,
    counter_value: int,
    suffix: str,
) -> str:
    if len(obl_code) != 2 or not obl_code.isdigit():
        raise ValueError("obl_code must be a 2-digit string.")

    counter_6_digits = str(counter_value).zfill(6)
    body_8_digits = f"{obl_code}{counter_6_digits}"
    check_digit = calculate_check_digit(body_8_digits)
    return f"{package_type}{body_8_digits}{check_digit}{suffix}"


async def generate_barcode_number(session: AsyncSession, package_type: str) -> str:
    items = await generate_barcode_numbers(
        session=session,
        package_type=package_type,
        quantity=1,
    )
    return items[0]


async def generate_barcode_numbers(
    session: AsyncSession,
    package_type: str,
    quantity: int,
) -> list[str]:
    normalized_package_type = validate_package_type(package_type)
    validated_quantity = validate_quantity(quantity)

    async with session.begin():
        obl_code = await get_setting_value(session, "obl_code", DEFAULT_OBL_CODE)
        suffix = (await get_setting_value(session, "country_suffix", DEFAULT_COUNTRY_SUFFIX)).upper()

        result = await session.execute(
            select(BarcodeCounter)
            .where(BarcodeCounter.package_type == normalized_package_type)
            .with_for_update()
        )
        counter = result.scalar_one_or_none()

        if counter is None:
            raise CounterNotFoundError(
                f"Counter row for package_type '{normalized_package_type}' was not found."
            )

        start_value = counter.current_value + 1
        end_value = counter.current_value + validated_quantity

        if end_value > MAX_COUNTER_VALUE:
            raise ValueError("Counter exceeded the maximum 6-digit serial value.")

        counter.current_value = end_value
        await session.flush()

    return [
        build_barcode_number(
            package_type=normalized_package_type,
            obl_code=obl_code,
            counter_value=counter_value,
            suffix=suffix,
        )
        for counter_value in range(start_value, end_value + 1)
    ]
