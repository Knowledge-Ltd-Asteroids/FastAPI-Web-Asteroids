from sqlmodel import Field, Relationship, SQLModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .player_profile import PlayerProfile

class CosmeticShip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: str = Field(default="")
    price: int = Field(default=0)
    sprite: str = Field(default="default_ship.png")
    is_default: bool = Field(default=False)

    owned_by: list["OwnedShip"] = Relationship(back_populates="cosmetic_ship")


class OwnedShip(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipped: bool = False

    player_id: int = Field(foreign_key="playerprofile.id", index=True , ondelete="CASCADE")
    player: Optional["PlayerProfile"] = Relationship(back_populates="ships")

    cosmetic_ship_id: int = Field(foreign_key="cosmeticship.id", index=True)
    cosmetic_ship: Optional["CosmeticShip"] = Relationship(back_populates="owned_by")