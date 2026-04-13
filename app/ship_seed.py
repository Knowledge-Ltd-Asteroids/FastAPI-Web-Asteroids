from sqlmodel import Session, select
from app.models.ship import CosmeticShip

def ship_seed(engine):
    ships = [
        CosmeticShip(
            name="Blue Fighter",
            description="A nimble blue fighter ship.",
            price=100,
            sprite="Blue.png",
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