from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING
from pydantic import EmailStr
from pwdlib import PasswordHash

if TYPE_CHECKING:
    pass

class UserBase(SQLModel):
    username: str
    email: EmailStr

class UserCreate(SQLModel):
    username: str = Field(min_length=5, max_length=128)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    role: str = Field(default="user")

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    email: EmailStr = Field(unique=True)
    password: str
    role: str = Field(default="user")
    active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    profile: Optional["PlayerProfile"] = Relationship(back_populates="user")

    def check_password(self, plaintext_password: str) -> bool:
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)

class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, min_length=5, max_length=128)
    email: Optional[EmailStr] = Field(default=None, max_length=255)

class UserResponse(UserBase):
    id: int
    username: str
    created_at: datetime