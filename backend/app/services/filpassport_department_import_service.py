from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Department
from app.services.department_import_service import LEGACY_ROOT_CODE, LEGACY_ROOT_NAME

OBSOLETE_DEMO_ROOT_CODES = {"KZROOT"}


class FilPassportImportError(RuntimeError):
    pass


@dataclass(slots=True)
class FilPassportDepartmentRecord:
    external_id: str
    parent_external_id: str | None
    code: str
    parent_code: str | None
    name: str
    region: str
    department_type: str
    is_active: bool


@dataclass(slots=True)
class FilPassportImportResult:
    created: int
    updated: int
    deactivated: int
    skipped: int
    missing: int
    errors: list[str]
    source_url: str
    imported_at: datetime
    dry_run: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "created": self.created,
            "updated": self.updated,
            "deactivated": self.deactivated,
            "skipped": self.skipped,
            "missing": self.missing,
            "errors": self.errors,
            "source_url": self.source_url,
            "imported_at": self.imported_at,
            "dry_run": self.dry_run,
        }


def _clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _fetch_json(url: str, timeout_seconds: int) -> dict[str, object]:
    try:
        with urlopen(url, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8-sig").lstrip()
    except HTTPError as error:
        raise FilPassportImportError(
            f"FilPassport returned HTTP {error.code}."
        ) from error
    except (OSError, URLError) as error:
        raise FilPassportImportError(
            "Could not fetch departments from FilPassport."
        ) from error

    try:
        if raw.startswith("\ufeff"):
            raw = raw[1:]
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise FilPassportImportError("FilPassport response is not valid JSON.") from error

    if not isinstance(data, dict):
        raise FilPassportImportError("FilPassport response must be a JSON object.")
    return data


async def fetch_filpassport_departments() -> dict[str, object]:
    settings = get_settings()
    url = settings.filpassport_departments_url.strip()
    timeout_seconds = settings.filpassport_timeout_seconds
    if not url:
        raise FilPassportImportError("FILPASSPORT_DEPARTMENTS_URL is not configured.")
    if timeout_seconds < 1:
        raise FilPassportImportError("FILPASSPORT_TIMEOUT_SECONDS must be positive.")

    return await asyncio.to_thread(_fetch_json, url, timeout_seconds)


def _is_active(row: dict[str, object]) -> bool:
    value = _clean(row.get("Status")).lower()
    if value in {"inactive", "closed", "false", "закрыт", "закрыто"}:
        return False
    return True


def _record_from_row(
    row: dict[str, object],
    department_type: str,
    parent_external_id: str | None,
    parent_code: str | None,
) -> FilPassportDepartmentRecord | None:
    external_id = _clean(row.get("DepId"))
    code = _clean(row.get("Code"))
    name = _clean(row.get("PoName"))
    if not external_id or not code or not name:
        return None

    return FilPassportDepartmentRecord(
        external_id=external_id,
        parent_external_id=parent_external_id,
        code=code,
        parent_code=_clean(row.get("ParentCode")) or parent_code,
        name=name,
        region=_clean(row.get("Oblast")) or name,
        department_type=department_type,
        is_active=_is_active(row),
    )


def normalize_filpassport_response(
    payload: dict[str, object],
) -> tuple[list[FilPassportDepartmentRecord], list[str]]:
    result = payload.get("Result")
    if not isinstance(result, list):
        raise FilPassportImportError("FilPassport response does not contain Result list.")

    records: list[FilPassportDepartmentRecord] = []
    errors: list[str] = []

    for branch_row in result:
        if not isinstance(branch_row, dict):
            errors.append("Skipped non-object branch row.")
            continue

        branch = _record_from_row(
            branch_row,
            department_type="branch",
            parent_external_id=LEGACY_ROOT_CODE,
            parent_code=LEGACY_ROOT_CODE,
        )
        if branch is None:
            errors.append("Skipped branch row without DepId, Code, or PoName.")
            continue
        records.append(branch)

        rups_rows = branch_row.get("level")
        if not isinstance(rups_rows, list):
            continue

        for rups_row in rups_rows:
            if not isinstance(rups_row, dict):
                errors.append(f"Skipped non-object RUPS row under {branch.code}.")
                continue

            rups = _record_from_row(
                rups_row,
                department_type="rups",
                parent_external_id=branch.external_id,
                parent_code=branch.code,
            )
            if rups is None:
                errors.append(f"Skipped RUPS row under {branch.code} without required fields.")
                continue
            records.append(rups)

            department_rows = rups_row.get("level2")
            if not isinstance(department_rows, list):
                continue

            for department_row in department_rows:
                if not isinstance(department_row, dict):
                    errors.append(f"Skipped non-object department row under {rups.code}.")
                    continue
                department = _record_from_row(
                    department_row,
                    department_type="department",
                    parent_external_id=rups.external_id,
                    parent_code=rups.code,
                )
                if department is None:
                    errors.append(
                        f"Skipped department row under {rups.code} without required fields."
                    )
                    continue
                records.append(department)

    return records, errors


def _build_full_paths(
    records_by_external_id: dict[str, FilPassportDepartmentRecord],
    departments_by_external_id: dict[str, Department],
    root_department: Department,
) -> dict[str, str]:
    path_cache = {LEGACY_ROOT_CODE: LEGACY_ROOT_NAME}

    def build(external_id: str) -> str:
        if external_id in path_cache:
            return path_cache[external_id]
        record = records_by_external_id[external_id]
        parent_external_id = record.parent_external_id or LEGACY_ROOT_CODE
        parent_path = (
            build(parent_external_id)
            if parent_external_id in records_by_external_id
            else root_department.full_path or LEGACY_ROOT_NAME
        )
        full_path = f"{parent_path} / {departments_by_external_id[external_id].name}"
        path_cache[external_id] = full_path
        return full_path

    return {external_id: build(external_id) for external_id in records_by_external_id}


def _collect_obsolete_demo_departments(departments: list[Department]) -> set[int]:
    roots = {
        department.id
        for department in departments
        if department.code in OBSOLETE_DEMO_ROOT_CODES
    }
    if not roots:
        return set()

    children_by_parent: dict[int, list[int]] = {}
    for department in departments:
        if department.parent_id is None:
            continue
        children_by_parent.setdefault(department.parent_id, []).append(department.id)

    obsolete_ids = set(roots)
    stack = list(roots)
    while stack:
        parent_id = stack.pop()
        for child_id in children_by_parent.get(parent_id, []):
            if child_id in obsolete_ids:
                continue
            obsolete_ids.add(child_id)
            stack.append(child_id)

    return obsolete_ids


def _deactivate_obsolete_demo_departments(departments: list[Department]) -> int:
    obsolete_ids = _collect_obsolete_demo_departments(departments)
    deactivated = 0
    for department in departments:
        if department.id not in obsolete_ids or not department.is_active:
            continue
        department.is_active = False
        deactivated += 1
    return deactivated


async def import_departments_from_filpassport(
    session: AsyncSession,
    dry_run: bool = False,
) -> FilPassportImportResult:
    settings = get_settings()
    source_url = settings.filpassport_departments_url.strip()
    payload = await fetch_filpassport_departments()
    records, errors = normalize_filpassport_response(payload)
    imported_at = datetime.now(timezone.utc)

    records_by_external_id = {record.external_id: record for record in records}
    external_ids = {LEGACY_ROOT_CODE, *records_by_external_id.keys()}
    codes = {LEGACY_ROOT_CODE, *(record.code for record in records)}

    created = 0
    updated = 0
    deactivated = 0
    skipped = 0

    if dry_run:
        missing_result = await session.execute(
            select(func.count())
            .select_from(Department)
            .where(Department.external_id.is_not(None))
            .where(Department.external_id.not_in(external_ids))
        )
        missing = int(missing_result.scalar_one() or 0)
        result = await session.execute(
            select(Department).where(
                (Department.external_id.in_(external_ids))
                | (Department.code.in_(codes))
            )
        )
        existing = list(result.scalars().all())
        all_departments_result = await session.execute(select(Department))
        all_departments = list(all_departments_result.scalars().all())
        obsolete_department_ids = _collect_obsolete_demo_departments(all_departments)
        deactivated = sum(
            1
            for department in all_departments
            if department.id in obsolete_department_ids and department.is_active
        )
        departments_by_external_id = {
            department.external_id: department
            for department in existing
            if department.external_id
        }
        departments_by_code = {department.code: department for department in existing}
        for record in records:
            department = departments_by_external_id.get(record.external_id) or departments_by_code.get(record.code)
            if department is None:
                created += 1
            else:
                updated += 1
        if LEGACY_ROOT_CODE not in departments_by_code and LEGACY_ROOT_CODE not in departments_by_external_id:
            created += 1
        return FilPassportImportResult(
            created=created,
            updated=updated,
            deactivated=deactivated,
            skipped=skipped,
            missing=missing,
            errors=errors,
            source_url=source_url,
            imported_at=imported_at,
            dry_run=True,
        )

    async with session.begin():
        missing_result = await session.execute(
            select(func.count())
            .select_from(Department)
            .where(Department.external_id.is_not(None))
            .where(Department.external_id.not_in(external_ids))
        )
        missing = int(missing_result.scalar_one() or 0)
        result = await session.execute(
            select(Department).where(
                (Department.external_id.in_(external_ids))
                | (Department.code.in_(codes))
            )
        )
        existing = list(result.scalars().all())
        all_departments_result = await session.execute(select(Department))
        all_departments = list(all_departments_result.scalars().all())
        deactivated = _deactivate_obsolete_demo_departments(all_departments)

        departments_by_external_id = {
            department.external_id: department
            for department in existing
            if department.external_id
        }
        departments_by_code = {department.code: department for department in existing}

        root_department = departments_by_code.get(LEGACY_ROOT_CODE) or departments_by_external_id.get(LEGACY_ROOT_CODE)
        if root_department is None:
            root_department = Department(
                external_id=LEGACY_ROOT_CODE,
                code=LEGACY_ROOT_CODE,
                name=LEGACY_ROOT_NAME,
                region="",
                parent_id=None,
                department_type="root",
                full_path=LEGACY_ROOT_NAME,
                is_active=True,
            )
            session.add(root_department)
            created += 1
        else:
            root_department.external_id = root_department.external_id or LEGACY_ROOT_CODE
            root_department.code = LEGACY_ROOT_CODE
            root_department.name = LEGACY_ROOT_NAME
            root_department.region = ""
            root_department.parent_id = None
            root_department.department_type = "root"
            root_department.full_path = LEGACY_ROOT_NAME
            root_department.is_active = True
            updated += 1

        departments_by_external_id[LEGACY_ROOT_CODE] = root_department
        departments_by_code[LEGACY_ROOT_CODE] = root_department

        for record in records:
            department = departments_by_external_id.get(record.external_id)
            if department is None:
                department = departments_by_code.get(record.code)

            code_owner = departments_by_code.get(record.code)
            if code_owner is not None and department is not None and code_owner.id != department.id:
                skipped += 1
                errors.append(
                    f"Skipped {record.code}: code already belongs to department id {code_owner.id}."
                )
                continue

            if department is None:
                department = Department(
                    external_id=record.external_id,
                    code=record.code,
                    name=record.name,
                    region=record.region,
                    department_type=record.department_type,
                    is_active=record.is_active,
                )
                session.add(department)
                created += 1
            else:
                department.external_id = department.external_id or record.external_id
                department.code = record.code
                department.name = record.name
                department.region = record.region
                department.department_type = record.department_type
                department.is_active = record.is_active
                updated += 1

            departments_by_external_id[record.external_id] = department
            departments_by_code[record.code] = department

        await session.flush()

        for record in records:
            department = departments_by_external_id.get(record.external_id)
            if department is None:
                continue
            parent_department = (
                departments_by_external_id.get(record.parent_external_id or "")
                or departments_by_code.get(record.parent_code or "")
                or root_department
            )
            department.parent_id = parent_department.id

        full_paths = _build_full_paths(
            records_by_external_id=records_by_external_id,
            departments_by_external_id=departments_by_external_id,
            root_department=root_department,
        )
        for external_id, full_path in full_paths.items():
            department = departments_by_external_id.get(external_id)
            if department is not None:
                department.full_path = full_path
        root_department.full_path = LEGACY_ROOT_NAME

    return FilPassportImportResult(
        created=created,
        updated=updated,
        deactivated=deactivated,
        skipped=skipped,
        missing=missing,
        errors=errors,
        source_url=source_url,
        imported_at=imported_at,
        dry_run=False,
    )
