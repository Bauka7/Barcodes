from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.regions import OFFICIAL_SHPI_BRANCH_CODES, KAZPOST_REGION_CODES
from app.models import BarcodeCodeCatalog, BarcodeCounter

SHPI_COUNTER_MAX_VALUE = 999_999


def get_counter_status(counter_exists: bool, current_value: int) -> str:
    if not counter_exists or current_value == 0:
        return "gray"

    if current_value >= SHPI_COUNTER_MAX_VALUE:
        return "red"

    return "green"


async def get_shpi_map(session: AsyncSession) -> dict[str, object]:
    catalog_result = await session.execute(select(BarcodeCodeCatalog.code))
    counter_result = await session.execute(
        select(
            BarcodeCounter.package_type,
            BarcodeCounter.region_code,
            BarcodeCounter.current_value,
        )
    )

    catalog_codes = {code for code in catalog_result.scalars().all()}
    counter_rows = list(counter_result.all())
    counter_codes = {row.package_type for row in counter_rows}
    codes = sorted(catalog_codes | counter_codes)
    counter_by_key = {
        (row.package_type, row.region_code): row.current_value
        for row in counter_rows
    }

    cells: list[dict[str, int | str]] = []
    for code in codes:
        for region_code in KAZPOST_REGION_CODES:
            key = (code, region_code)
            counter_exists = key in counter_by_key
            value = int(counter_by_key.get(key) or 0)
            cells.append(
                {
                    "code": code,
                    "region_code": region_code,
                    "current_value": value,
                    "status": get_counter_status(
                        counter_exists=counter_exists,
                        current_value=value,
                    ),
                }
            )

    return {
        "regions": OFFICIAL_SHPI_BRANCH_CODES,
        "region_codes": KAZPOST_REGION_CODES,
        "codes": codes,
        "cells": cells,
    }
