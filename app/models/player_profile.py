from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .ship import PlayerShip
    from .game_session import GameSessionPlayer

class PlayerProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    highest_solo_score: int = 0
    highest_coop_score: int = 0
    solo_games_played: int = 0
    coop_games_played: int = 0
    asteroids_destroyed: int = 0
    currency: int = 0
    last_played: Optional[datetime] = None

    user: Optional["User"] = Relationship(back_populates="profile")
    ships: list["PlayerShip"] = Relationship(back_populates="owners")
    game_sessions: list["GameSessionPlayer"] = Relationship(back_populates="player")