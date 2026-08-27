from uuid import UUID

from pydantic import BaseModel


class CurrentUserRead(BaseModel):
    id: UUID
    email: str
