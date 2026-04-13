from sqlmodel import Session, select
from app.models.ship import CosmeticShip

def ship_seed(engine):
    ships = [
        CosmeticShip(
            name="Classic",
            description="The starter ship. Reliable and nimble.",
            price=0,
            sprite="spaceship_thrust.png",
            is_default=True
        ),
        CosmeticShip(
            name="Blue Fighter",
            description="A nimble blue fighter built for speed.",
            price=100,
            sprite="Blue.png",
            is_default=False
        ),
        CosmeticShip(
            name="Brown Cruiser",
            description="A heavy cruiser built to last.",
            price=200,
            sprite="brown.png",
            is_default=False
        ),
        CosmeticShip(
            name="Gray Scout",
            description="A fast scout ship for quick maneuvers.",
            price=300,
            sprite="Gray1.png",
            is_default=False
        ),
        CosmeticShip(
            name="Green Hornet",
            description="A rare green ship with a deadly sting.",
            price=400,
            sprite="green.png",
            is_default=False
        ),
        CosmeticShip(
            name="Purple Phantom",
            description="A mysterious purple ship feared by all.",
            price=600,
            sprite="purple.png",
            is_default=False
        ),
    ]
    with Session(engine) as session:
        for ship in ships:
            existing = session.exec(
                select(CosmeticShip).where(CosmeticShip.name == ship.name)
            ).first()
            if not existing:
                session.add(ship)
        session.commit()