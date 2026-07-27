import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.providers import service
from app.providers.schemas import ProviderCreateSchema, ProviderResponseSchema

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("", response_model=ProviderResponseSchema, status_code=201)
async def create_provider(
    provider_create: ProviderCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new provider.
    Args:
        provider_create (ProviderCreateSchema): The schema containing the provider data to create.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        ProviderResponseSchema: The newly created provider instance.
    """
    provider = await service.create_provider_service(db, provider_create)
    return provider


@router.get("/{provider_id}", response_model=ProviderResponseSchema)
async def get_provider_by_id(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a provider by its ID.
    Args:
        provider_id (uuid.UUID): The ID of the provider to retrieve.
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        ProviderResponseSchema | None: The provider instance if found, otherwise None.
    """
    provider = await service.get_provider_by_id_service(db, provider_id)
    return provider


@router.get("", response_model=list[ProviderResponseSchema])
async def get_all_providers(
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve all providers.
    Args:
        db (AsyncSession): The SQLAlchemy session to use for the database operation.
    Returns:
        list[ProviderResponseSchema]: A list of all provider instances.
    """
    providers = await service.get_all_providers_service(db)
    return providers
