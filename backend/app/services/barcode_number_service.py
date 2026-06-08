from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeCounter

VALID_PACKAGE_TYPES = {
    "GP",
    "CE",
    "AV",
    "UP",
    "CO",
    "GB",
    "CZ",
    "GF",
    "RR",
    "RZ",
}
CHECK_DIGIT_WEIGHTS = (8, 6, 4, 2, 3, 5, 9, 7)
COUNTRY_SUFFIX = "KZ"
MAX_SERIAL_VALUE = 999_999_999


def validate_package_type(package_type: str) -> str:
    normalized_package_type = package_type.strip().upper()

    if normalized_package_type not in VALID_PACKAGE_TYPES:
        raise ValueError("Invalid package_type.")

    return normalized_package_type


def validate_quantity(quantity: int) -> int:
    if quantity < 1 or quantity > 1000:
        raise ValueError("quantity must be between 1 and 1000.")

    return quantity


def calculate_check_digit(serial_9_digits: str) -> int:
    if len(serial_9_digits) != 9 or not serial_9_digits.isdigit():
        raise ValueError("serial_9_digits must be a 9-digit string.")

    weighted_sum = sum(
        int(digit) * weight
        for digit, weight in zip(serial_9_digits[:8], CHECK_DIGIT_WEIGHTS, strict=True)
    )
    remainder = weighted_sum % 11
    check_digit = 11 - remainder

    if check_digit == 10:
        return 0

    if check_digit == 11:
        return 5

    return check_digit


def build_barcode_number(package_type: str, counter_value: int) -> str:
    serial_9_digits = str(counter_value).zfill(9)
    check_digit = calculate_check_digit(serial_9_digits)
    return f"{package_type}{serial_9_digits}{check_digit}{COUNTRY_SUFFIX}"


async def generate_barcode_number(session: AsyncSession, package_type: str) -> str:
    items = await generate_barcode_numbers(session=session, package_type=package_type, quantity=1)
    return items[0]


async def generate_barcode_numbers(
    session: AsyncSession,
    package_type: str,
    quantity: int,
) -> list[str]:
    normalized_package_type = validate_package_type(package_type)
    validated_quantity = validate_quantity(quantity)

    async with session.begin():
        result = await session.execute(
            select(BarcodeCounter)
            .where(BarcodeCounter.package_type == normalized_package_type)
            .with_for_update()
        )
        counter = result.scalar_one_or_none()

        if counter is None:
            raise ValueError(f"Counter for package type '{normalized_package_type}' was not found.")

        start_value = counter.current_value + 1
        end_value = counter.current_value + validated_quantity

        if end_value > MAX_SERIAL_VALUE:
            raise ValueError("Counter exceeded the maximum 9-digit serial value.")

        counter.current_value = end_value
        await session.flush()

    return [
        build_barcode_number(normalized_package_type, counter_value)
        for counter_value in range(start_value, end_value + 1)
    ]
