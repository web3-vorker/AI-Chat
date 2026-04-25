from pydantic import BaseModel, Field

class ChatHistorySchema(BaseModel):
  id: int = Field(default=None)
  user_ip_address: str
  user_message: str
  ai_response: str