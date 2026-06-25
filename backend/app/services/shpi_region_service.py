import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AppSetting, Department

DEFAULT_SHPI_REGION_CODE = "01"

logger = logging.getLogger(__name__)


def _normalize_setting_region_code(value: str | None) -> str | None:
    normalized = (value or "").strip()
    if len(normalized) == 2 and normalized.isdigit():
        return normalized
    return None


async def get_inherited_department_shpi_region_code(
    session: AsyncSession,
    department_id: int | None,
) -> str | None:
    if department_id is None:
        return None

    visited_ids: set[int] = set()
    current_id: int | None = department_id

    while current_id is not None and current_id not in visited_ids:
        visited_ids.add(current_id)
        result = await session.execute(
            select(
                Department.id,
                Department.parent_id,
                Department.shpi_region_code,
            ).where(Department.id == current_id)
        )
        department = result.one_or_none()
        if department is None:
            return None

        shpi_region_code = _normalize_setting_region_code(department.shpi_region_code)
        if shpi_region_code is not None:
            return shpi_region_code

        current_id = department.parent_id

    return None


async def get_fallback_shpi_region_code(session: AsyncSession) -> str:
    result = await session.execute(select(AppSetting).where(AppSetting.key == "obl_code"))
    setting = result.scalar_one_or_none()
    configured_code = _normalize_setting_region_code(setting.value if setting else None)
    return configured_code or DEFAULT_SHPI_REGION_CODE


async def resolve_generation_shpi_region_code(
    session: AsyncSession,
    department_id: int | None,
) -> str:
    shpi_region_code = await get_inherited_department_shpi_region_code(
        session=session,
        department_id=department_id,
    )
    if shpi_region_code is not None:
        return shpi_region_code

    fallback_code = await get_fallback_shpi_region_code(session=session)
    logger.warning(
        "Using fallback SHPI region code '%s' for department_id=%s.",
        fallback_code,
        department_id,
    )
    return fallback_code
