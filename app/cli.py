import typer
import csv
from tabulate import tabulate
from sqlmodel import select
from app.database import create_db_and_tables, get_cli_session, drop_all
from app.models import *
from app.utilities.security import encrypt_password


cli = typer.Typer()

@cli.command()
def initialize():
    with get_cli_session() as db:
        drop_all()
        create_db_and_tables()

        password = encrypt_password("password")
        
        users = [
            User(username="bob", email="bob@mail.com", password=password, currency=2000, role="user"),
            User(username="alice", email="alice@mail.com", password=password, currency=1500, role="user"),
        ]
        for user in users:
            db.add(user)
        db.commit()
        
        cosmetic_ships = [
            CosmeticShip(
                name="Classic Arrow",
                description="The original classic spaceship design",
                price=0,
                sprite="classic_arrow.png",
                is_default=True
            ),
            CosmeticShip(
                name="Plasma Dart",
                description="A sleek blue spacecraft with plasma energy",
                price=500,
                sprite="plasma_dart.png",
                is_default=False
            ),
            CosmeticShip(
                name="Neon Viper",
                description="Neon green serpentine ship with sharp angles",
                price=750,
                sprite="neon_viper.png",
                is_default=False
            ),
            CosmeticShip(
                name="Golden Phoenix",
                description="Majestic gold ship with phoenix-like wings",
                price=1000,
                sprite="golden_phoenix.png",
                is_default=False
            ),
            CosmeticShip(
                name="Obsidian Shadow",
                description="Dark obsidian ship that seems to absorb light",
                price=1200,
                sprite="obsidian_shadow.png",
                is_default=False
            ),
        ]

        for ship in cosmetic_ships:
            db.add(ship)
        db.commit()
        
        owned_ships = [
            # Bob's ships
            OwnedShip(user_id=1, cosmetic_ship_id=1),  # Classic Arrow (free)
            OwnedShip(user_id=1, cosmetic_ship_id=2),  # Plasma Dart
            OwnedShip(user_id=1, cosmetic_ship_id=3),  # Neon Viper

            # Alice's ships
            OwnedShip(user_id=2, cosmetic_ship_id=1),  # Classic Arrow (free)
            OwnedShip(user_id=2, cosmetic_ship_id=4),  # Golden Phoenix
        ]

        for owned_ship in owned_ships:
            db.add(owned_ship)
        db.commit()

        print("Database Initialized")
    
@cli.command()
def test():
    print("Testing the cli")

if __name__ == "__main__":
    cli()