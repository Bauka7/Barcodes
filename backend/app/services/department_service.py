from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

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
) -> list[Department]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = select(Department).order_by(Department.parent_id, Department.name)

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


async def get_departments_tree(session: AsyncSession) -> list[dict[str, object]]:
    statement = select(Department).order_by(Department.parent_id, Department.name)
    result = await session.execute(statement)
    departments = list(result.scalars().all())

    nodes_by_id: dict[int, dict[str, object]] = {}
    roots: list[dict[str, object]] = []

    for department in departments:
        nodes_by_id[department.id] = {
            "id": department.id,
            "code": department.code,
            "name": department.name,
            "department_type": department.department_type,
            "full_path": department.full_path,
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
