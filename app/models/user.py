from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING
from pydantic import EmailStr
from pwdlib import PasswordHash

if TYPE_CHECKING:
    from .player_profile import PlayerProfile
    from .ship import Ship

class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    role: str

# class UserCreate(SQLModel):
#     username: str = Field(min_length=5, max_length=128)
#     email: EmailStr = Field(max_length=255)
#     password: str = Field(min_length=8, max_length=128)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def check_password(self, plaintext_password:str):
        return PasswordHash.recommended().verify(password=plaintext_password, hash=self.password)
    
    profile: Optional["PlayerProfile"] = Relationship(back_populates="user")

class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, min_length=5, max_length=128)
    email: Optional[EmailStr] = Field(default=None, max_length=255)

class UserResponse(UserBase):
    id: int
    username: str
    created_at: datetime