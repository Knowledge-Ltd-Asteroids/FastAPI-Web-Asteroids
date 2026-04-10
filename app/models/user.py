from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import EmailStr
from pwdlib import PasswordHash


class UserCreate(SQLModel):
    username:str
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)

class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role:str = ""

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    def check_password(self, plaintext_password:str):
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)
    
class AdminCreate(UserBase):
    role:str = "admin"

class RegularUserCreate(UserBase):
    role:str = "regular_user"
