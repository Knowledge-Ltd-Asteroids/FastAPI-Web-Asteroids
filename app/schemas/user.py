from app.models.user import UserBase
from sqlmodel import SQLModel, Field
from pydantic import EmailStr
from typing import Optional


class UserUpdate(SQLModel):
    username: Optional[str]
    email: Optional[EmailStr]
 
class AdminCreate(UserBase):
    role:str = "admin"

class RegularUserCreate(UserBase):
    role:str = "regular_user"
    password: str = Field(min_length=8, max_length=128)

class UserResponse(SQLModel):
    id: int
    username:str
    email: EmailStr

class SignupRequest(SQLModel):
    username: str
    email: EmailStr
    password: str
