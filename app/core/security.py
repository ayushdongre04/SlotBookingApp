import uuid
from datetime import date, datetime, timedelta, UTC

import jwt
from passlib.context import CryptContext

from app.core.config import settings

# Argon2id specifically — the hybrid variant OWASP recommends, balancing
# resistance to GPU-parallelized cracking with resistance to side-channel
# timing attacks. deprecated="auto" means if a second scheme is ever added
# later, passlib re-hashes old hashes transparently on next successful
# login — no manual migration.
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

ALGORITHM = "HS256"

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID) -> str:
    """
    tenant_id is embedded directly in the token claims.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),  # subject — who this token belongs to
        "tenant_id": str(tenant_id),
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
        "iat": now,  # issued at
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    """Raises jwt.PyJWTError (or a subclass) on any invalid/expired/
    tampered token — callers translate that into a 401, they don't
    inspect the exception type themselves."""
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])