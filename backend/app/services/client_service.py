from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Client
from app.schemas import ClientCreate, ClientUpdate


def _normalize_client_name(name: str) -> str:
    normalized_name = name.strip()

    if not normalized_name:
        raise ValueError("name is required.")

    return normalized_name


def _validate_pagination(limit: int, offset: int) -> tuple[int, int]:
    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100.")

    if offset < 0:
        raise ValueError("offset must be greater than or equal to 0.")

    return limit, offset


async def get_client_by_id(
    session: AsyncSession,
    client_id: int,
) -> Client | None:
    result = await session.execute(select(Client).where(Client.id == client_id))
    return result.scalar_one_or_none()


async def get_client_by_name(
    session: AsyncSession,
    name: str,
) -> Client | None:
    result = await session.execute(select(Client).where(Client.name == name))
    return result.scalar_one_or_none()


async def create_client(
    session: AsyncSession,
    payload: ClientCreate,
) -> Client:
    normalized_name = _normalize_client_name(payload.name)
    existing_client = await get_client_by_name(session=session, name=normalized_name)

    if existing_client is not None:
        raise ValueError(f"Client '{normalized_name}' already exists.")

    client = Client(
        name=normalized_name,
        contact_person=payload.contact_person,
        contact_phone=payload.contact_phone,
        email=str(payload.email) if payload.email is not None else None,
        notes=payload.notes,
        is_active=payload.is_active,
    )
    session.add(client)
    await session.flush()
    return client


async def update_client(
    session: AsyncSession,
    client: Client,
    payload: ClientUpdate,
) -> Client:
    updated_fields = payload.model_fields_set

    if "name" in updated_fields and payload.name is not None:
        normalized_name = _normalize_client_name(payload.name)
        existing_client = await get_client_by_name(session=session, name=normalized_name)

        if existing_client is not None and existing_client.id != client.id:
            raise ValueError(f"Client '{normalized_name}' already exists.")

        client.name = normalized_name

    if "contact_person" in updated_fields:
        client.contact_person = payload.contact_person

    if "contact_phone" in updated_fields:
        client.contact_phone = payload.contact_phone

    if "email" in updated_fields:
        client.email = str(payload.email) if payload.email is not None else None

    if "notes" in updated_fields:
        client.notes = payload.notes

    if "is_active" in updated_fields and payload.is_active is not None:
        client.is_active = payload.is_active

    return client


async def list_clients(
    session: AsyncSession,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
    is_active: bool | None = None,
) -> list[Client]:
    validated_limit, validated_offset = _validate_pagination(limit, offset)
    statement = select(Client).order_by(Client.name)

    if search:
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                Client.name.ilike(pattern),
                Client.contact_person.ilike(pattern),
                Client.contact_phone.ilike(pattern),
                Client.email.ilike(pattern),
            )
        )

    if is_active is not None:
        statement = statement.where(Client.is_active == is_active)

    statement = statement.limit(validated_limit).offset(validated_offset)
    result = await session.execute(statement)
    return list(result.scalars().all())
