import uuid

from pydantic.type_adapter import P
from sqlalchemy import select


from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.model import Provider
from app.providers.schemas import ProviderCreateSchema


async def create_provider(
    db: AsyncSession,
    provider_create: ProviderCreateSchema,
    tenant_id: uuid.UUID
) -> Provider:
    """
    Create a new provider in the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        provider_create (ProviderCreateSchema): The schema containing the provider data to create.
    Returns:
        Provider: The newly created provider instance.
    """
    provider = Provider(name=provider_create.name, tenant_id=tenant_id)
    db.add(provider)  # Add the new provider instance to the session
    await db.flush()  # Flush to get the ID assigned by the database
    await db.refresh(provider)  # Refresh to get the latest state from the database
    return provider


async def get_provider_by_id(db: AsyncSession, provider_id: uuid.UUID, tenant_id: uuid.UUID) -> Provider | None:
    """
    Retrieve a provider from the database by its ID.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
        provider_id (uuid.UUID): The ID of the provider to retrieve.
    Returns:
        Provider | None: The provider instance if found, otherwise None.
    """
    result = await db.execute(select(Provider).where(
        Provider.id == provider_id,
        Provider.tenant_id == tenant_id
    ))

    return result.scalar_one_or_none()


async def get_all_providers(db: AsyncSession, tenant_id: uuid.UUID) -> list[Provider]:
    """
    Retrieve all providers from the database.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        list[Provider]: A list of all provider instances.
    """
    result = await db.execute(select(Provider).where(Provider.tenant_id == tenant_id))
    return result.scalars().all()
