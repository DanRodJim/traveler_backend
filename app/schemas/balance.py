from pydantic import BaseModel
import uuid


class SettleRequest(BaseModel):
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    currency: str