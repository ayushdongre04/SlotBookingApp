import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProviderCreateSchema(BaseModel):
    # The ... is Python's Ellipsis object. Implies that this field is required.
    name: str = Field(..., max_length=120)


class ProviderResponseSchema(BaseModel):
    # configDict is usually used in ResponseSchema classes to allow Pydantic to read from ORM objects.
    # from_attributes=True allows Pydantic to read from ORM objects (like SQLAlchemy models)
    # and convert them into Pydantic models.
    # example: ProviderResponseSchema.model_validate(provider_instance)
    # will create a Pydantic model from a SQLAlchemy model instance.
    # without from_attributes=True, Pydantic would expect a dict-like object instead of an ORM model.
    # example: ProviderResponseSchema.model_validate({"id": "some-uuid", "name": "Provider Name"})
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    name: str



