import argparse
import asyncio

from app.db.database import AsyncSessionLocal
from app.services.filpassport_department_import_service import (
    FilPassportImportError,
    import_departments_from_filpassport,
)


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import official KazPost departments from FilPassport API."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and parse data, but do not write departments.",
    )
    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        try:
            result = await import_departments_from_filpassport(
                session=session,
                dry_run=args.dry_run,
            )
        except FilPassportImportError as error:
            raise SystemExit(f"FilPassport import failed: {error}") from error

    print(f"Source URL: {result.source_url}")
    print(f"Dry run: {result.dry_run}")
    print(f"Created departments: {result.created}")
    print(f"Updated departments: {result.updated}")
    print(f"Skipped departments: {result.skipped}")
    print(f"Missing from source: {result.missing}")
    if result.errors:
        print("Errors:")
        for error in result.errors:
            print(f"- {error}")


if __name__ == "__main__":
    asyncio.run(main())
