from fastapi import APIRouter, Depends, Path, Request, Response
from authx import RequestToken

from backend.db.database import SessionDep
from backend.auth.services.service import AuthService
from backend.auth.schemas.user import UserCredentials
from backend.auth.config.config import security

auth_router = APIRouter(prefix="/auth")


def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session)


@auth_router.post("/register", tags=["auth"])
async def register(
    credentials: UserCredentials,
    service: AuthService = Depends(get_auth_service)
) -> dict:
    return await service.register(credentials)


@auth_router.post("/login", tags=["auth"])
async def login(
    credentials: UserCredentials,
    response: Response,
    service: AuthService = Depends(get_auth_service)
) -> dict:
    return await service.login(credentials, response)


@auth_router.get("/me", tags=["auth"])
async def get_current_user(
  request: Request,
  service: AuthService = Depends(get_auth_service),
  token: RequestToken = Depends(security.access_token_required)
  ) -> dict:
    user = await service.get_current_user(token)
    return {"email": user.email}