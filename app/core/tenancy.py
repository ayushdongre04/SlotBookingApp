import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.core.security import decode_access_token

# HTTPBearer extracts "Authorization: Bearer <token>" and 401s
# automatically if the header is missing or malformed — before our code
# even runs. auto_error=True (the default) is what gives us that for free.
bearer_scheme = HTTPBearer()

async def get_current_tenant_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> uuid.UUID:
    """
    tenant_id now comes from a cryptographically signed JWT claim, not a client-supplied
    header — a client can no longer claim an arbitrary tenant by simply setting a header,
    since the token is verified against settings.secret_key before this value is trusted.
    """
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return uuid.UUID(payload["tenant_id"])

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> uuid.UUID:
    """Same decode, returning the user identity instead of the tenant —
    for any future endpoint that needs to know WHO is asking, not just
    which tenant."""
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return uuid.UUID(payload["sub"])
