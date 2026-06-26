import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.regions import OFFICIAL_SHPI_BRANCH_CODE_SET
from app.models import BarcodeCounter

logger = logging.getLogger(__name__)

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PACKAGE_TYPE_RE = re.compile(r"^[A-Z]{2}$")


class OfficialShpiDisabledError(RuntimeError):
    """Raised when the official SHPI DB integration is disabled."""


class OfficialShpiConfigurationError(RuntimeError):
    """Raised when safe SQL identifiers or database URL are not configured."""


class OfficialShpiConnectionError(RuntimeError):
    """Raised for safe external DB connection/query failures."""


@dataclass(frozen=True)
class OfficialShpiCounter:
    package_type: str
    region_code: str
    current_value: int
    used_count: int
    last_used_date: datetime | None


@dataclass(frozen=True)
class OfficialShpiPreviewRow:
    barcode: str
    registered_at: datetime | None
    package_type: str
    region_code: str
    sequence_number: int
    check_digit: str
    country: str


@dataclass(frozen=True)
class OfficialShpiSyncResult:
    total_official_counters: int
    created: int
    updated: int
    unchanged: int
    skipped_invalid_package_type: int
    skipped_invalid_region_code: int

    def to_dict(self) -> dict[str, int | str]:
        return {
            "total_official_counters": self.total_official_counters,
            "created": self.created,
            "updated": self.updated,
            "unchanged": self.unchanged,
            "skipped_invalid_package_type": self.skipped_invalid_package_type,
            "skipped_invalid_region_code": self.skipped_invalid_region_code,
            "message": "Official SHPI counters synced to local barcode_counters.",
        }


def _normalize_async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url

    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    return database_url


def _quoted_identifier(identifier: str) -> str:
    normalized = identifier.strip()
    if not _IDENTIFIER_RE.fullmatch(normalized):
        raise OfficialShpiConfigurationError("Official SHPI identifier is not valid.")

    return f'"{normalized}"'


def _qualified_table_name(table_name: str) -> str:
    parts = [part.strip() for part in table_name.split(".") if part.strip()]
    if len(parts) not in {1, 2}:
        raise OfficialShpiConfigurationError("Official SHPI table name is not valid.")

    return ".".join(_quoted_identifier(part) for part in parts)


def _official_sql_parts() -> tuple[str, str, str]:
    settings = get_settings()
    return (
        _qualified_table_name(settings.official_shpi_table),
        _quoted_identifier(settings.official_shpi_barcode_column),
        _quoted_identifier(settings.official_shpi_date_column),
    )


def _ensure_enabled() -> str:
    settings = get_settings()
    if not settings.official_shpi_db_enabled:
        raise OfficialShpiDisabledError("Official SHPI database integration is disabled.")

    if not settings.official_shpi_database_url.strip():
        raise OfficialShpiConfigurationError(
            "OFFICIAL_SHPI_DATABASE_URL is required when official SHPI integration is enabled."
        )

    return _normalize_async_database_url(settings.official_shpi_database_url.strip())


@asynccontextmanager
async def _official_connection() -> AsyncIterator[AsyncConnection]:
    database_url = _ensure_enabled()
    engine = None

    try:
        engine = create_async_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "application_name": "qazpostweb_official_shpi_readonly",
                    "default_transaction_read_only": "on",
                },
            },
        )
        async with engine.connect() as connection:
            yield connection
    except OfficialShpiDisabledError:
        raise
    except OfficialShpiConfigurationError:
        raise
    except Exception as error:
        logger.warning(
            "Official SHPI database query failed with %s.",
            error.__class__.__name__,
        )
        raise OfficialShpiConnectionError(
            "Official SHPI database is unavailable."
        ) from error
    finally:
        if engine is not None:
            await engine.dispose()


async def test_connection() -> dict[str, bool | str]:
    """Check that the external read-only DB, table, and configured columns are reachable."""

    settings = get_settings()
    if not settings.official_shpi_db_enabled:
        return {
            "enabled": False,
            "ok": False,
            "message": "Official SHPI database integration is disabled.",
        }

    table_name, barcode_column, date_column = _official_sql_parts()
    statement = text(
        f"""
        SELECT {barcode_column} AS barcode, {date_column} AS registered_at
        FROM {table_name}
        LIMIT 1
        """
    )

    async with _official_connection() as connection:
        await connection.execute(statement)

    return {
        "enabled": True,
        "ok": True,
        "message": "Official SHPI database connection is OK.",
    }


async def preview(limit: int = 20) -> list[OfficialShpiPreviewRow]:
    validated_limit = max(1, min(limit, 100))
    table_name, barcode_column, date_column = _official_sql_parts()
    statement = text(
        f"""
        SELECT
            {barcode_column} AS barcode,
            {date_column} AS registered_at,
            substring({barcode_column} from 1 for 2) AS package_type,
            substring({barcode_column} from 3 for 2) AS region_code,
            CAST(substring({barcode_column} from 5 for 6) AS integer) AS sequence_number,
            substring({barcode_column} from 11 for 1) AS check_digit,
            substring({barcode_column} from 12 for 2) AS country
        FROM {table_name}
        WHERE {barcode_column} ~ '^[A-Z]{{2}}[0-9]{{9}}KZ$'
          AND substring({barcode_column} from 5 for 6) ~ '^[0-9]{{6}}$'
        ORDER BY {date_column} DESC NULLS LAST
        LIMIT :limit
        """
    )

    async with _official_connection() as connection:
        result = await connection.execute(statement, {"limit": validated_limit})
        row_mappings = result.mappings().all()

    rows: list[OfficialShpiPreviewRow] = []
    for row in row_mappings:
        rows.append(
            OfficialShpiPreviewRow(
                barcode=row["barcode"],
                registered_at=row["registered_at"],
                package_type=row["package_type"],
                region_code=row["region_code"],
                sequence_number=row["sequence_number"],
                check_digit=row["check_digit"],
                country=row["country"],
            )
        )
    return rows


async def get_counters() -> list[OfficialShpiCounter]:
    table_name, barcode_column, date_column = _official_sql_parts()
    statement = text(
        f"""
        SELECT
            substring({barcode_column} from 1 for 2) AS package_type,
            substring({barcode_column} from 3 for 2) AS region_code,
            MAX(CAST(substring({barcode_column} from 5 for 6) AS integer)) AS current_value,
            COUNT(*) AS used_count,
            MAX({date_column}) AS last_used_date
        FROM {table_name}
        WHERE {barcode_column} ~ '^[A-Z]{{2}}[0-9]{{9}}KZ$'
          AND substring({barcode_column} from 5 for 6) ~ '^[0-9]{{6}}$'
        GROUP BY
            substring({barcode_column} from 1 for 2),
            substring({barcode_column} from 3 for 2)
        ORDER BY package_type, region_code
        """
    )

    async with _official_connection() as connection:
        result = await connection.execute(statement)
        row_mappings = result.mappings().all()

    counters: list[OfficialShpiCounter] = []
    for row in row_mappings:
        counters.append(
            OfficialShpiCounter(
                package_type=row["package_type"],
                region_code=row["region_code"],
                current_value=int(row["current_value"] or 0),
                used_count=int(row["used_count"] or 0),
                last_used_date=row["last_used_date"],
            )
        )
    return counters


async def sync_counters_to_local_db(session: AsyncSession) -> OfficialShpiSyncResult:
    """Sync official external counters into local barcode_counters without decreasing values."""

    official_counters = await get_counters()
    created = 0
    updated = 0
    unchanged = 0
    skipped_invalid_package_type = 0
    skipped_invalid_region_code = 0

    for official_counter in official_counters:
        if not _PACKAGE_TYPE_RE.fullmatch(official_counter.package_type):
            skipped_invalid_package_type += 1
            continue

        if official_counter.region_code not in OFFICIAL_SHPI_BRANCH_CODE_SET:
            skipped_invalid_region_code += 1
            continue

        result = await session.execute(
            select(BarcodeCounter)
            .where(BarcodeCounter.package_type == official_counter.package_type)
            .where(BarcodeCounter.region_code == official_counter.region_code)
            .with_for_update()
        )
        local_counter = result.scalar_one_or_none()

        if local_counter is None:
            try:
                async with session.begin_nested():
                    session.add(
                        BarcodeCounter(
                            package_type=official_counter.package_type,
                            region_code=official_counter.region_code,
                            current_value=official_counter.current_value,
                        )
                    )
                    await session.flush()
            except IntegrityError:
                logger.info(
                    "Local counter for package_type=%s and region_code=%s was created concurrently; re-querying.",
                    official_counter.package_type,
                    official_counter.region_code,
                )
                result = await session.execute(
                    select(BarcodeCounter)
                    .where(BarcodeCounter.package_type == official_counter.package_type)
                    .where(BarcodeCounter.region_code == official_counter.region_code)
                    .with_for_update()
                )
                local_counter = result.scalar_one_or_none()
                if local_counter is None:
                    raise
            else:
                created += 1
                continue

        if local_counter is None:
            raise LookupError(
                "Local barcode counter could not be created or reloaded safely."
            )

        if official_counter.current_value > local_counter.current_value:
            local_counter.current_value = official_counter.current_value
            updated += 1
        else:
            unchanged += 1

    await session.flush()
    return OfficialShpiSyncResult(
        total_official_counters=len(official_counters),
        created=created,
        updated=updated,
        unchanged=unchanged,
        skipped_invalid_package_type=skipped_invalid_package_type,
        skipped_invalid_region_code=skipped_invalid_region_code,
    )
