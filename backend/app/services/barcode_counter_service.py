import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.regions import OFFICIAL_SHPI_BRANCH_CODE_SET
from app.models import BarcodeCounter

logger = logging.getLogger(__name__)


async def get_or_create_official_counter_for_update(
    session: AsyncSession,
    package_type: str,
    region_code: str,
) -> BarcodeCounter | None:
    """Return a locked counter row, creating missing official-region rows at 0.

    Existing counters are never overwritten. Missing counters are created only for
    official SHPI branch region codes. The unique constraint on
    (package_type, region_code) is used to handle concurrent creation safely.
    """

    statement = (
        select(BarcodeCounter)
        .where(BarcodeCounter.package_type == package_type)
        .where(BarcodeCounter.region_code == region_code)
        .with_for_update()
    )
    result = await session.execute(statement)
    counter = result.scalar_one_or_none()
    if counter is not None:
        return counter

    if region_code not in OFFICIAL_SHPI_BRANCH_CODE_SET:
        logger.warning(
            "Counter for package_type=%s and non-official region_code=%s was not found.",
            package_type,
            region_code,
        )
        return None

    try:
        async with session.begin_nested():
            session.add(
                BarcodeCounter(
                    package_type=package_type,
                    region_code=region_code,
                    current_value=0,
                )
            )
            await session.flush()
    except IntegrityError:
        logger.info(
            "Counter for package_type=%s and region_code=%s was created concurrently; re-querying.",
            package_type,
            region_code,
        )
    else:
        logger.info(
            "Created missing official SHPI counter for package_type=%s and region_code=%s.",
            package_type,
            region_code,
        )

    result = await session.execute(statement)
    return result.scalar_one_or_none()
