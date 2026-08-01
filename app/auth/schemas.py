import uuid

from pydantic import BaseModel, EmailStr, ConfigDict, class_validators, field_validator


class RegisterRequest(BaseModel):
    tenant_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_minimum_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("password must be at least 8 characters")
        return value


class LoginRequest(BaseModel):
    # tenant_id is required here because email is unique PER TENANT, not
    # globally — the same email can exist under multiple tenants as
    # separate accounts, so email alone can't identify a unique user.
    tenant_id: uuid.UUID
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str


class RegisterResponse(BaseModel):
    user: UserResponse
    tenant_id: uuid.UUID


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
