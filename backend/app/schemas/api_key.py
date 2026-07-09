from pydantic import BaseModel, Field, field_validator
import re
from uuid import UUID

class MakeAPIKey(BaseModel):
    name:str = Field(
        ...,
        min_length=6,
        max_length=100
    )
    @field_validator("name")
    @classmethod
    def validate_name(cls,n:str)->str:
        if not re.fullmatch(r"[\w -]+", n):
            raise ValueError("Name can only contain letters, numbers, spaces, hyphens, and underscores")
        return n
    


class APIKeyCreationResponse(BaseModel):
    key_id:UUID
    key_name:str
    raw_key:str

from datetime import datetime

class APIKeyResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True  # "If you are handed a database object instead of a dictionary, don't crash. Automatically extract the fields directly from the object attributes." -> definitio on this
