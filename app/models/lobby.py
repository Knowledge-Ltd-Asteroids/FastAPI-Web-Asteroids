from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING
import secrets

if TYPE_CHECKING:
    from .user import User

class Lobby(SQLModel, table=True):
    """Game lobby for multiplayer rooms"""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    creator_id: int = Field(foreign_key="user.id")
    creator: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Lobby.creator_id", "cascade": "all, delete-orphan"}
    )
    
    invited_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    invited_user: Optional["User"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "Lobby.invited_user_id", "cascade": "all, delete-orphan"}
    )
    
    invite_code: str = Field(unique=True, index=True)
    status: str = Field(default="waiting")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    winner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    creator_score: int = Field(default=0)
    invited_player_score: int = Field(default=0)
    
    @staticmethod
    def generate_invite_code() -> str:
        return secrets.token_hex(4).upper()

class LobbyResponse(SQLModel):
    id: int
    invite_code: str
    creator_id: int
    invited_user_id: Optional[int]
    status: str
    created_at: datetime
