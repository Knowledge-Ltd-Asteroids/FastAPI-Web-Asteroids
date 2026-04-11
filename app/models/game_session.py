from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .player_profile import PlayerProfile

class GameSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    game_mode: str = Field(default="solo")

    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None

    total_score: int = 0
    total_asteroids_destroyed: int = 0
    total_time_seconds: int = 0

    players: list["GameSessionPlayer"] = Relationship(back_populates="session")


class GameSessionPlayer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="gamesession.id")
    player_id: int = Field(foreign_key="playerprofile.id")

    # Stats for a single player
    score: int = 0
    asteroids_destroyed: int = 0
    currency_earned: int = 0

    # This is for co-op only
    is_host: bool = False
    is_ready: bool = Field(default=False)
    connected: bool = Field(default=True)

    session: Optional["GameSession"] = Relationship(back_populates="players")
    player: Optional["PlayerProfile"] = Relationship(back_populates="game_sessions")