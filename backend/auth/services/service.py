# Service

from fastapi import HTTPException, Response
from sqlalchemy import select

from backend.auth.security.password import hash_password, verify_password, create_access_token
from backend.auth.config.config import config
from backend.auth.models.user import UserModel
from backend.db.database import SessionDep
from backend.auth.schemas.user import UserCredentials


class AuthService:
  def __init__(self, session: SessionDep):
    self.session = session

  async def register(self, credentials: UserCredentials) -> dict:
    query = select(UserModel).where(UserModel.email == credentials.email)
    result = await self.session.execute(query)
    existing_user = result.scalar_one_or_none()
    if existing_user:
      raise HTTPException(status_code=400, detail="User with this email already exists")
    
    hashed_password = hash_password(credentials.password)

    new_user = UserModel(
      email = credentials.email,
      password_hash = hashed_password
    )

    self.session.add(new_user)
    await self.session.commit()
    return {"message": "✅ User created"}

  async def login(self, credentials: UserCredentials, response: Response) -> dict:
    query = select(UserModel).where(UserModel.email == credentials.email)
    result = await self.session.execute(query)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(credentials.password, user.password_hash):
      raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(uid=str(user.id))
    response.set_cookie(key=config.JWT_ACCESS_COOKIE_NAME, value=token, httponly=True, samesite="lax")
    return {"access_token": token}


  # Получение данных текущего пользователя из JWT токена
  async def get_current_user(
      self,
      token
  ) -> UserModel:
      user_id = int(token.sub)
      query = select(UserModel).where(UserModel.id == user_id)
      result = await self.session.execute(query)
      user = result.scalar_one_or_none()

      if not user:
          raise HTTPException(status_code=404, detail="User not found")
      
      return user

