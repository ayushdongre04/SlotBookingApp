import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ValidationError
from app.core.security import hash_password, verify_password, create_access_token
from app.auth.model import User
from app.auth.schemas import RegisterRequest, LoginRequest
from app.tenants.model import Tenant


async def register_user(db: AsyncSession, payload: RegisterRequest) -> tuple[User, uuid.UUID]:
    """Creates a new Tenant AND its first User in one transaction —
    self-service signup, not an invite-into-existing-tenant flow."""
    tenant = Tenant(name=payload.tenant_name)
    db.add(tenant)
    await db.flush()  # assigns tenant.id without committing yet — needed
    # so the User row below can reference it via tenant_id in the SAME
    # transaction. If User creation fails, the tenant insert rolls back
    # too, since nothing has committed.

    existing = await db.execute(
        select(User).where(User.tenant_id == tenant.id, User.email == payload.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Email {payload.email} already registered for this tenant")

    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await db.refresh(tenant)

    return user, tenant.id


async def authenticate_user(db: AsyncSession, payload: LoginRequest) -> str:
    """Returns a signed JWT access token on success. Deliberately raises
    the SAME error (ValidationError, generic message) whether the email
    doesn't exist for this tenant OR the password is wrong — distinguishing
    the two would let an attacker enumerate which emails are registered."""
    result = await db.execute(
        select(User).where(User.tenant_id == payload.tenant_id, User.email == payload.email)
    )
    user = result.scalar_one_or_none()

    if user is None or not verify_password(payload.password, user.hashed_password):
        raise ValidationError("Invalid email or password")

    return create_access_token(user_id=user.id, tenant_id=user.tenant_id)