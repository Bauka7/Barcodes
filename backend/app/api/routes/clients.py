from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.models import Client, User
from app.schemas import ClientCreate, ClientRead, ClientUpdate
from app.services.audit_service import create_audit_log
from app.services.auth_service import require_roles
from app.services.client_service import (
    create_client,
    get_client_by_id,
    list_clients,
    update_client,
)

router = APIRouter(prefix="/clients", tags=["clients"])


def _client_to_schema(client: Client) -> ClientRead:
    return ClientRead(
        id=client.id,
        name=client.name,
        contact_person=client.contact_person,
        contact_phone=client.contact_phone,
        email=client.email,
        notes=client.notes,
        is_active=client.is_active,
        created_at=client.created_at,
        updated_at=client.updated_at,
    )


@router.get("", response_model=list[ClientRead], status_code=status.HTTP_200_OK)
async def get_clients(
    search: str | None = Query(default=None),
    limit: int = Query(default=100),
    offset: int = Query(default=0),
    is_active: bool | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> list[ClientRead]:
    try:
        clients = await list_clients(
            session=session,
            search=search,
            limit=limit,
            offset=offset,
            is_active=is_active,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return [_client_to_schema(client) for client in clients]


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
async def create_client_endpoint(
    payload: ClientCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> ClientRead:
    try:
        async with session.begin():
            client = await create_client(session=session, payload=payload)
            await create_audit_log(
                session=session,
                action="client_created",
                user=current_user,
                request=request,
                entity_type="client",
                entity_id=str(client.id),
                details={"name": client.name},
            )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _client_to_schema(client)


@router.get("/{client_id}", response_model=ClientRead, status_code=status.HTTP_200_OK)
async def get_client_endpoint(
    client_id: int,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin", "operator")),
) -> ClientRead:
    client = await get_client_by_id(session=session, client_id=client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with id {client_id} was not found.",
        )

    return _client_to_schema(client)


@router.patch("/{client_id}", response_model=ClientRead, status_code=status.HTTP_200_OK)
async def update_client_endpoint(
    client_id: int,
    payload: ClientUpdate,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles("admin")),
) -> ClientRead:
    try:
        async with session.begin():
            client = await get_client_by_id(session=session, client_id=client_id)

            if client is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Client with id {client_id} was not found.",
                )

            await update_client(session=session, client=client, payload=payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    return _client_to_schema(client)
