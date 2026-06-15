from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import User
from app.schemas.shpi_map import ShpiMapResponse
from app.services.auth_service import require_roles
from app.services.shpi_map_service import get_shpi_map

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/shpi-map",
    response_model=ShpiMapResponse,
    status_code=status.HTTP_200_OK,
)
async def get_admin_shpi_map(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> ShpiMapResponse:
    data = await get_shpi_map(session=session)
    return ShpiMapResponse.model_validate(data)
