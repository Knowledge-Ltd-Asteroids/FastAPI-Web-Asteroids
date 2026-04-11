from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .player_profile import PlayerProfile

class Ship(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    description: str
    price: int
    sprite: str
    is_default: bool = False

    owners: list["PlayerShip"] = Relationship(back_populates="ship")

class PlayerShip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ship_id: int = Field(foreign_key="ship.id")
    player_id: int = Field(foreign_key="playerprofile.id")

    equipped: bool = False

    player: Optional["PlayerProfile"] = Relationship(back_populates="ships")
    ship: Optional["Ship"] = Relationship(back_populates="owners")