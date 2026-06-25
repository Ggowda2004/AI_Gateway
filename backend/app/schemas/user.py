from pydantic import BaseModel, EmailStr, Field
import re

class CreateUser(BaseModel):
    email:EmailStr
    password:str = Field(
        ...,
        max_length=31,
        min_length=8,
        pattern=re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d).(?=.*[^\w\s]).*$")
    )

class LoginUser(BaseModel):
    email:EmailStr
    password:str = Field(min_length=8)