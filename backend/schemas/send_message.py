from pydantic import BaseModel


class SendMessageOut(BaseModel):
    user_message: str
    ai_response: str

