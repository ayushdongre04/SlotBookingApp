from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db_session import get_db
from app.auth import service
from app.auth.schemas import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user, tenant_id = await service.register_user(db, payload)
    return RegisterResponse(user=user, tenant_id=tenant_id)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    token = await service.authenticate_user(db, payload)
    return TokenResponse(access_token=token)
