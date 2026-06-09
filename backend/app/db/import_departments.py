import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.models import AppSetting
from app.services.department_import_service import (
    DEFAULT_LEGACY_DBF_PATH,
    import_departments_from_dbf,
)


async def _resolve_dbf_path(path_argument: str | None) -> str:
    if path_argument:
        return str(Path(path_argument))

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AppSetting).where(AppSetting.key == "legacy_dbf_path")
        )
        setting = result.scalar_one_or_none()

        if setting is None:
            return DEFAULT_LEGACY_DBF_PATH

        value = setting.value.strip()
        if not value:
            return DEFAULT_LEGACY_DBF_PATH

        return value


async def main_async() -> None:
    path_argument = sys.argv[1] if len(sys.argv) > 1 else None
    dbf_path = await _resolve_dbf_path(path_argument)

    async with AsyncSessionLocal() as session:
        result = await import_departments_from_dbf(session=session, dbf_path=dbf_path)

    print(f"DBF path: {result['dbf_path']}")
    print(f"Processed rows: {result['processed']}")
    print(f"Created departments: {result['created']}")
    print(f"Updated departments: {result['updated']}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
