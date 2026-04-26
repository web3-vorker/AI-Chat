from fastapi import Depends
from authx import RequestToken
from backend.db.database import SessionDep
from backend.auth.services.service import AuthService
from backend.auth.config.config import security
from backend.auth.models.user import UserModel


async def get_current_user(
    session: SessionDep,
    token: RequestToken = Depends(security.access_token_required)
) -> UserModel:
    service = AuthService(session)
    return await service.get_current_user(token)