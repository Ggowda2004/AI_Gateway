from pydantic import BaseModel, Field, field_validator
import re

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