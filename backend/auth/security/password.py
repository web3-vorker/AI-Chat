# Хеширование паролей
import bcrypt

from backend.auth.config.config import security as _authx


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

access_token_required = _authx.access_token_required
create_access_token = _authx.create_access_token