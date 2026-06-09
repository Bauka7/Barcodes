import asyncio

from app.db.database import AsyncSessionLocal
from app.schemas import UserCreate
from app.services.auth_service import create_user, get_user_by_username

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


async def create_default_admin() -> None:
    async with AsyncSessionLocal() as session:
        existing_admin = await get_user_by_username(
            session=session,
            username=DEFAULT_ADMIN_USERNAME,
        )

        if existing_admin is not None:
            print("Default admin user already exists. Skipped.")
            return

        await create_user(
            session=session,
            payload=UserCreate(
                username=DEFAULT_ADMIN_USERNAME,
                password=DEFAULT_ADMIN_PASSWORD,
                full_name="Default Administrator",
                role="admin",
                is_active=True,
            ),
        )
        await session.commit()

    print("Created default admin user.")
    print(f"Username: {DEFAULT_ADMIN_USERNAME}")
    print(f"Password: {DEFAULT_ADMIN_PASSWORD}")
    print("WARNING: Change this password immediately after first login.")


def main() -> None:
    asyncio.run(create_default_admin())


if __name__ == "__main__":
    main()
