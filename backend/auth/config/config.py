# Настройка AuthX

from authx import AuthX, AuthXConfig
import os

config = AuthXConfig()
config.JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
config.JWT_ALGORITHM = "HS256"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["headers", "cookies"] 

security = AuthX(config=config)
