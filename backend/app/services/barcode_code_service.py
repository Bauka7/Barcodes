from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BarcodeCodeCatalog, BarcodeCounter
from app.services.barcode_number_service import validate_package_type

CATALOG_STATUSES = {"available", "active", "reserved", "blocked", "deprecated"}
# Статусы, из которых код разрешено выдавать клиенту при одобрении.
ALLOCATABLE_STATUSES = {"available", "active"}


def _validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def list_catalog_codes(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    status: str | None = None,
) -> list[BarcodeCodeCatalog]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = select(BarcodeCodeCatalog).order_by(BarcodeCodeCatalog.code)

    if status:
        normalized_status = status.strip().lower()
        if normalized_status not in CATALOG_STATUSES:
            raise ValueError(
                "status must be one of: available, active, reserved, blocked, deprecated."
            )
        statement = statement.where(BarcodeCodeCatalog.status == normalized_status)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_catalog_code(
    session: AsyncSession,
    code: str,
) -> BarcodeCodeCatalog | None:
    normalized_code = validate_package_type(code)
    result = await session.execute(
        select(BarcodeCodeCatalog).where(BarcodeCodeCatalog.code == normalized_code)
    )
    return result.scalar_one_or_none()


async def ensure_code_allocatable(
    session: AsyncSession,
    code: str,
) -> str:
    """Проверяет, что код можно выдать, и помечает его активным.

    Требования: код есть в справочнике со статусом available/active и под него
    существует счётчик barcode_counters (иначе генерировать нечем). При первой
    выдаче статус available -> active. Возвращает нормализованный код.
    """

    normalized_code = validate_package_type(code)

    catalog_entry = await get_catalog_code(session=session, code=normalized_code)
    if catalog_entry is None:
        raise ValueError(f"Code '{normalized_code}' is not in the catalog.")

    if catalog_entry.status not in ALLOCATABLE_STATUSES:
        raise ValueError(
            f"Code '{normalized_code}' is not allocatable (status: {catalog_entry.status})."
        )

    counter_result = await session.execute(
        select(BarcodeCounter).where(BarcodeCounter.package_type == normalized_code)
    )
    if counter_result.scalar_one_or_none() is None:
        raise ValueError(f"Code '{normalized_code}' has no counter to generate from.")

    if catalog_entry.status == "available":
        catalog_entry.status = "active"

    return normalized_code
