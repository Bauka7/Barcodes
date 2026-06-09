from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from dbfread import DBF
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Department

DEFAULT_LEGACY_DBF_PATH = r"C:\QazPost\BarCodes new\Dbf_win.dbf"
LEGACY_ROOT_CODE = "9999"
LEGACY_ROOT_NAME = "\u0410\u041e \u041a\u0430\u0437\u043f\u043e\u0447\u0442\u0430"


@dataclass(slots=True)
class LegacyDepartmentRecord:
    code: str
    parent_code: str
    name: str
    region: str


def _normalize_text(value: object) -> str:
    if value is None:
        return ""

    return str(value).strip()


def _load_legacy_departments(dbf_path: str | Path) -> list[LegacyDepartmentRecord]:
    path = Path(dbf_path)

    if not path.exists():
        raise ValueError(f"DBF file was not found: {path}")

    records = DBF(
        str(path),
        encoding="cp1251",
        ignore_missing_memofile=True,
        char_decode_errors="ignore",
    )

    departments: list[LegacyDepartmentRecord] = []
    for row in records:
        code = _normalize_text(row.get("ID"))
        parent_code = _normalize_text(row.get("ID_HI")) or LEGACY_ROOT_CODE
        name = _normalize_text(row.get("DEPNAME_PS"))
        region = _normalize_text(row.get("OBL"))

        if not code or not name:
            continue

        departments.append(
            LegacyDepartmentRecord(
                code=code,
                parent_code=parent_code,
                name=name,
                region=region,
            )
        )

    return departments


def _get_department_type(
    code: str,
    parent_code: str | None,
    child_codes: dict[str, list[str]],
) -> str:
    if code == LEGACY_ROOT_CODE:
        return "root"

    if parent_code == LEGACY_ROOT_CODE:
        return "branch"

    if child_codes.get(code):
        return "group"

    return "department"


async def import_departments_from_dbf(
    session: AsyncSession,
    dbf_path: str | Path,
) -> dict[str, int | str]:
    legacy_departments = _load_legacy_departments(dbf_path)
    child_codes: dict[str, list[str]] = defaultdict(list)
    rows_by_code = {record.code: record for record in legacy_departments}

    for record in legacy_departments:
        child_codes[record.parent_code].append(record.code)

    created_count = 0
    updated_count = 0

    async with session.begin():
        all_codes = {LEGACY_ROOT_CODE, *rows_by_code.keys()}
        result = await session.execute(
            select(Department).where(Department.code.in_(all_codes))
        )
        existing_departments = {
            department.code: department for department in result.scalars().all()
        }

        root_department = existing_departments.get(LEGACY_ROOT_CODE)
        if root_department is None:
            root_department = Department(
                code=LEGACY_ROOT_CODE,
                name=LEGACY_ROOT_NAME,
                region="",
                department_type="root",
                full_path=LEGACY_ROOT_NAME,
            )
            session.add(root_department)
            existing_departments[LEGACY_ROOT_CODE] = root_department
            created_count += 1
        else:
            root_department.name = LEGACY_ROOT_NAME
            root_department.region = ""
            root_department.department_type = "root"
            root_department.full_path = LEGACY_ROOT_NAME
            root_department.parent_id = None
            updated_count += 1

        for record in legacy_departments:
            department = existing_departments.get(record.code)
            department_type = _get_department_type(
                code=record.code,
                parent_code=record.parent_code,
                child_codes=child_codes,
            )

            if department is None:
                department = Department(
                    code=record.code,
                    name=record.name,
                    region=record.region,
                    department_type=department_type,
                )
                session.add(department)
                existing_departments[record.code] = department
                created_count += 1
            else:
                department.name = record.name
                department.region = record.region
                department.department_type = department_type
                updated_count += 1

        await session.flush()

        for record in legacy_departments:
            department = existing_departments[record.code]
            parent_department = existing_departments.get(record.parent_code, root_department)
            department.parent_id = parent_department.id

        path_cache = {LEGACY_ROOT_CODE: LEGACY_ROOT_NAME}

        def build_full_path(code: str) -> str:
            if code in path_cache:
                return path_cache[code]

            record = rows_by_code[code]
            parent_path = build_full_path(record.parent_code)
            full_path = f"{parent_path} / {existing_departments[code].name}"
            path_cache[code] = full_path
            return full_path

        for record in legacy_departments:
            existing_departments[record.code].full_path = build_full_path(record.code)

        root_department.full_path = LEGACY_ROOT_NAME

    return {
        "dbf_path": str(Path(dbf_path)),
        "processed": len(legacy_departments),
        "created": created_count,
        "updated": updated_count,
    }
