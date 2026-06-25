from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.regions import OFFICIAL_SHPI_BRANCH_NAME_BY_CODE
from app.models import Department


def _validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 1000:
        raise ValueError("limit must be between 1 and 1000.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def list_departments(
    session: AsyncSession,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    department_ids: list[int] | None = None,
) -> list[Department]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = (
        select(Department)
        .where(Department.is_active.is_(True))
        .order_by(Department.parent_id, Department.name)
    )

    if department_ids is not None:
        if not department_ids:
            return []
        statement = statement.where(Department.id.in_(department_ids))

    normalized_search = (search or "").strip()
    if normalized_search:
        pattern = f"%{normalized_search}%"
        statement = statement.where(
            or_(
                Department.code.ilike(pattern),
                Department.name.ilike(pattern),
                Department.region.ilike(pattern),
                Department.full_path.ilike(pattern),
            )
        )

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def list_departments_missing_shpi_region(
    session: AsyncSession,
) -> list[Department]:
    result = await session.execute(
        select(Department)
        .where(Department.is_active.is_(True))
        .where(Department.shpi_region_code.is_(None))
        .order_by(Department.parent_id, Department.name)
    )
    return list(result.scalars().all())


async def get_departments_tree(
    session: AsyncSession,
    department_ids: list[int] | None = None,
) -> list[dict[str, object]]:
    statement = (
        select(Department)
        .where(Department.is_active.is_(True))
        .order_by(Department.parent_id, Department.name)
    )
    if department_ids is not None:
        if not department_ids:
            return []
        statement = statement.where(Department.id.in_(department_ids))

    result = await session.execute(statement)
    departments = list(result.scalars().all())

    nodes_by_id: dict[int, dict[str, object]] = {}
    roots: list[dict[str, object]] = []

    for department in departments:
        nodes_by_id[department.id] = {
            "id": department.id,
            "external_id": department.external_id,
            "code": department.code,
            "name": department.name,
            "shpi_region_code": department.shpi_region_code,
            "shpi_region_name": (
                OFFICIAL_SHPI_BRANCH_NAME_BY_CODE.get(department.shpi_region_code)
                if department.shpi_region_code
                else None
            ),
            "department_type": department.department_type,
            "full_path": department.full_path,
            "is_active": department.is_active,
            "children": [],
        }

    for department in departments:
        node = nodes_by_id[department.id]
        if department.parent_id is None:
            roots.append(node)
            continue

        parent_node = nodes_by_id.get(department.parent_id)
        if parent_node is None:
            roots.append(node)
            continue

        parent_node["children"].append(node)

    return roots
