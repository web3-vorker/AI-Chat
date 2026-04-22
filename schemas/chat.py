from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime

