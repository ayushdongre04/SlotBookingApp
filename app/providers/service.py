import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError

from app.providers import repository
from app.providers.model import Provider
from app.providers.schemas import ProviderCreateSchema

logger = logging.getLogger(__name__)

async def create_provider_service(
    db: AsyncSession,
    provider_create: ProviderCreateSchema,
    tenant_id: uuid.UUID
) -> Provider:

    provider = await repository.create_provider(
        db,
        provider_create,
        tenant_id
    )

    await db.commit()

    return provider


async def get_provider_by_id_service(
    db: AsyncSession,
    provider_id: uuid.UUID,
    tenant_id: uuid.UUID,
) -> Provider | None:

    provider = await repository.get_provider_by_id(
        db,
        provider_id,
        tenant_id
    )

    if not provider:
        logger.warning(f"Provider with ID {provider_id} not found.")
        raise NotFoundError(f"Provider with ID {provider_id} not found.")
    else:
        logger.info(f"Retrieved provider: {provider}")

    return provider

async def get_all_providers_service(
    db: AsyncSession,
    tenant_id: uuid.UUID
) -> list[Provider]:

    providers = await repository.get_all_providers(db, tenant_id)

    return providers