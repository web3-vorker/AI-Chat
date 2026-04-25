from dotenv import load_dotenv
import os

load_dotenv()

class AppConfig:
  def __init__(self):
    self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    self.openrouter_model = os.getenv("OPENROUTER_MODEL", "inclusionai/ling-2.6-flash:free")
    self.openrouter_site_url = os.getenv("OPENROUTER_SITE_URL")
    self.openrouter_app_name = os.getenv("OPENROUTER_APP_NAME")
    self.MAX_MESSAGES_IN_CONTEXT = int(os.getenv("MAX_MESSAGES_IN_CONTEXT", "20"))
    self.MAX_CHAT_TITLE_LENGTH = int(os.getenv("MAX_CHAT_TITLE_LENGTH", "100"))
    self.SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    self.COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
    samesite = os.getenv("COOKIE_SAMESITE", "strict").lower()
    self.COOKIE_SAMESITE = samesite if samesite in {"lax", "strict", "none"} else "strict"


app_config = AppConfig()
