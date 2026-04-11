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
    with get_cli_session() as db: # Get a connection to the database
        drop_all() # delete all tables
        create_db_and_tables() #recreate all tables

        password = encrypt_password("password")
        
        users = [
            User(username="bob", email="bob@mail.com", password=password, role="regular_user"),
            User(username="alice", email="alice@mail.com", password=password, role="regular_user"),
            User(username="admin", email="admin@mail.com", password=password, role="admin"),
        ]
        for user in users:
            db.add(user)
        db.commit()
        
        profiles = [
            PlayerProfile(user_id=1, highest_solo_score=12500, 
                         solo_games_played=15, asteroids_destroyed=342, currency=1500),
            PlayerProfile(user_id=2, highest_solo_score=8900, 
                         solo_games_played=8, asteroids_destroyed=156, currency=750),
            PlayerProfile(user_id=3, highest_solo_score=50000, 
                         solo_games_played=42, asteroids_destroyed=1200, currency=9999),
        ]
        for profile in profiles:
            db.add(profile)
        db.commit()

        
        ships = [
            Ship(name="ship1", description="Ship1 description", 
                 price=0, sprite="ship1.png", is_default=True),
            Ship(name="ship2", description="Ship2 description", 
                 price=500, sprite="ship2.png"),
            Ship(name="ship3", description="Ship 3 description", 
                 price=1000, sprite="ship3.png"),
        ]
        for ship in ships:
            db.add(ship)
        db.commit()
        
        player_ships = [
            PlayerShip(player_id=1, ship_id=1, equipped=False),
            PlayerShip(player_id=1, ship_id=2, equipped=True),
            PlayerShip(player_id=1, ship_id=3, equipped=False),
            PlayerShip(player_id=2, ship_id=1, equipped=True),
            PlayerShip(player_id=3, ship_id=1, equipped=False),
            PlayerShip(player_id=3, ship_id=2, equipped=False),
            PlayerShip(player_id=3, ship_id=3, equipped=True),
        ]
        for ps in player_ships:
            db.add(ps)
        db.commit()

        print("Database Initialized")
    
@cli.command()
def test():
    print("Testing the cli")

if __name__ == "__main__":
    cli()