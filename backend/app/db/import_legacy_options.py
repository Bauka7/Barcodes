import asyncio

from app.db.database import AsyncSessionLocal
from app.services.legacy_options_import_service import (
    import_legacy_options,
    resolve_legacy_options_path,
)


async def main_async() -> None:
    options_path = resolve_legacy_options_path()

    async with AsyncSessionLocal() as session:
        result = await import_legacy_options(session=session, options_path=options_path)

    print(f"Options path: {result['options_path']}")
    print(f"Created counters: {result['created_counters']}")
    print(f"Updated counters: {result['updated_counters']}")
    print(f"Skipped counters: {result['skipped_counters']}")
    print(f"Created settings: {result['created_settings']}")
    print(f"Updated settings: {result['updated_settings']}")
    print(f"Skipped settings: {result['skipped_settings']}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
