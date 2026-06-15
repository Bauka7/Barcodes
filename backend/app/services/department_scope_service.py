from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department, User


class DepartmentScopeError(ValueError):
    pass


async def get_department_subtree_ids(
    session: AsyncSession,
    department_id: int,
) -> list[int]:
    result = await session.execute(
        select(Department.id, Department.parent_id).order_by(Department.id)
    )
    rows = result.all()
    existing_ids = {row.id for row in rows}

    if department_id not in existing_ids:
        raise DepartmentScopeError(f"Department with id {department_id} was not found.")

    children_by_parent: dict[int | None, list[int]] = {}
    for row in rows:
        children_by_parent.setdefault(row.parent_id, []).append(row.id)

    subtree_ids: list[int] = []
    stack = [department_id]
    while stack:
        current_id = stack.pop()
        subtree_ids.append(current_id)
        stack.extend(reversed(children_by_parent.get(current_id, [])))

    return subtree_ids


async def get_user_department_scope_ids(
    session: AsyncSession,
    user: User,
) -> list[int] | None:
    if user.role == "admin":
        return None

    if user.department_id is None:
        raise DepartmentScopeError(f"{user.role} user must have department_id.")

    if user.role == "operator":
        return await get_department_subtree_ids(
            session=session,
            department_id=user.department_id,
        )

    if user.role == "client":
        return [user.department_id]

    raise DepartmentScopeError("Unknown user role.")


async def can_access_department(
    session: AsyncSession,
    user: User,
    department_id: int | None,
) -> bool:
    if user.role == "admin":
        return True

    if department_id is None:
        return False

    scope_ids = await get_user_department_scope_ids(session=session, user=user)
    return scope_ids is None or department_id in scope_ids


async def require_department_access(
    session: AsyncSession,
    user: User,
    department_id: int | None,
) -> None:
    if not await can_access_department(
        session=session,
        user=user,
        department_id=department_id,
    ):
        raise DepartmentScopeError("Not enough permissions for this department.")
