import typer
from datetime import datetime, timezone, timedelta
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
            User(username="bob", email="bob@mail.com", password=password, role="regular_user"),
            User(username="alice", email="alice@mail.com", password=password, role="regular_user"),
            User(username="admin", email="admin@mail.com", password=password, role="admin"),
        ]
        for user in users:
            db.add(user)
        db.commit()
        
        profiles = [
            PlayerProfile(
                user_id=1, 
                display_name="bob",
                highest_solo_score=12500, 
                highest_coop_score=21000,
                solo_games_played=4, 
                coop_games_played=2,
                asteroids_destroyed=109, 
                currency=1500,
                total_seconds_played=435,
                last_played=datetime.now(timezone.utc) - timedelta(days=1)
            ),
            PlayerProfile(
                user_id=2, 
                display_name="alice",
                highest_solo_score=15000, 
                highest_coop_score=21000,
                solo_games_played=3, 
                coop_games_played=2,
                asteroids_destroyed=102, 
                currency=1000,
                total_seconds_played=415,
                last_played=datetime.now(timezone.utc) - timedelta(hours=5)
            ),
            PlayerProfile(
                user_id=3, 
                display_name="admin",
                highest_solo_score=9999, 
                highest_coop_score=9999,
                solo_games_played=999, 
                coop_games_played=9999,
                asteroids_destroyed=999, 
                currency=9999,
                total_seconds_played=999,
                last_played=datetime.now(timezone.utc) - timedelta(hours=5)
            )
        ]
        for profile in profiles:
            db.add(profile)
        db.commit()

        ships = [
            Ship(name="Starter Ship", description="Starter Ship description", 
                 price=0, sprite="spaceship_thrust.png", is_default=True),
            Ship(name="Ship2", description="Ship 2 description", 
                 price=500, sprite="spaceship_thrust.png"),
            Ship(name="Ship3", description="Ship 3 description", 
                 price=1000, sprite="spaceship_thrust.png"),
            Ship(name="Ship4", description="Ship4 description", 
                 price=2000, sprite="spaceship_thrust.png", is_default=True),
            Ship(name="Ship5", description="Ship 5 description", 
                 price=100, sprite="spaceship_thrust.png"),
            Ship(name="Ship6", description="Ship 6 description", 
                 price=500, sprite="spaceship_thrust.png"),
                 
        ]
        for ship in ships:
            db.add(ship)
        db.commit()
        
        player_ships = [
            PlayerShip(player_id=1, ship_id=1, equipped=False),
            PlayerShip(player_id=1, ship_id=2, equipped=True),
            PlayerShip(player_id=1, ship_id=3, equipped=False),
            PlayerShip(player_id=2, ship_id=1, equipped=True),
            PlayerShip(player_id=2, ship_id=2, equipped=False),
        ]
        for ps in player_ships:
            db.add(ps)
        db.commit()
        
        #Dummy session data to pass to profile page
        solo1 = GameSession(game_mode="solo")
        db.add(solo1)
        db.commit()
        db.refresh(solo1)
        
        solo1_player = GameSessionPlayer(
            session_id=solo1.id,
            player_id=1,
            score=12500,
            asteroids_destroyed=42,
            deaths=0,
            currency_earned=420
        )
        db.add(solo1_player)
        
        solo1.total_score = 12500
        solo1.total_asteroids_destroyed = 42
        solo1.total_time_seconds = 180
        solo1.started_at = datetime.now(timezone.utc) - timedelta(days=3)
        solo1.ended_at = datetime.now(timezone.utc) - timedelta(days=3, minutes=3)
        db.add(solo1)
        
        solo2 = GameSession(game_mode="solo")
        db.add(solo2)
        db.commit()
        db.refresh(solo2)
        
        solo2_player = GameSessionPlayer(
            session_id=solo2.id,
            player_id=1,
            score=8900,
            asteroids_destroyed=31,
            deaths=1,
            currency_earned=310
        )
        db.add(solo2_player)
        
        solo2.total_score = 8900
        solo2.total_asteroids_destroyed = 31
        solo2.total_time_seconds = 120
        solo2.started_at = datetime.now(timezone.utc) - timedelta(days=2)
        solo2.ended_at = datetime.now(timezone.utc) - timedelta(days=2, minutes=2)
        db.add(solo2)
        
        solo3 = GameSession(game_mode="solo")
        db.add(solo3)
        db.commit()
        db.refresh(solo3)
        
        solo3_player = GameSessionPlayer(
            session_id=solo3.id,
            player_id=1,
            score=6700,
            asteroids_destroyed=24,
            deaths=2,
            currency_earned=240
        )
        db.add(solo3_player)
        
        solo3.total_score = 6700
        solo3.total_asteroids_destroyed = 24
        solo3.total_time_seconds = 90
        solo3.started_at = datetime.now(timezone.utc) - timedelta(hours=30)
        solo3.ended_at = datetime.now(timezone.utc) - timedelta(hours=30, minutes=1, seconds=30)
        db.add(solo3)
        
        alice_solo1 = GameSession(game_mode="solo")
        db.add(alice_solo1)
        db.commit()
        db.refresh(alice_solo1)
        
        alice_solo1_player = GameSessionPlayer(
            session_id=alice_solo1.id,
            player_id=2,
            score=8900,
            asteroids_destroyed=31,
            deaths=0,
            currency_earned=310
        )
        db.add(alice_solo1_player)
        
        alice_solo1.total_score = 8900
        alice_solo1.total_asteroids_destroyed = 31
        alice_solo1.total_time_seconds = 130
        alice_solo1.started_at = datetime.now(timezone.utc) - timedelta(days=2, hours=12)
        alice_solo1.ended_at = datetime.now(timezone.utc) - timedelta(days=2, hours=12, minutes=2)
        db.add(alice_solo1)
        
        alice_solo2 = GameSession(game_mode="solo")
        db.add(alice_solo2)
        db.commit()
        db.refresh(alice_solo2)
        
        alice_solo2_player = GameSessionPlayer(
            session_id=alice_solo2.id,
            player_id=2,
            score=5200,
            asteroids_destroyed=19,
            deaths=1,
            currency_earned=190
        )
        db.add(alice_solo2_player)
        
        alice_solo2.total_score = 5200
        alice_solo2.total_asteroids_destroyed = 19
        alice_solo2.total_time_seconds = 75
        alice_solo2.started_at = datetime.now(timezone.utc) - timedelta(hours=20)
        alice_solo2.ended_at = datetime.now(timezone.utc) - timedelta(hours=20, minutes=1)
        db.add(alice_solo2)
        
        alice_solo3 = GameSession(game_mode="solo")
        db.add(alice_solo3)
        db.commit()
        db.refresh(alice_solo3)
        
        alice_solo3_player = GameSessionPlayer(
            session_id=alice_solo3.id,
            player_id=2,
            score=15000,
            asteroids_destroyed=52,
            deaths=0,
            currency_earned=520
        )
        db.add(alice_solo3_player)
        
        alice_solo3.total_score = 15000
        alice_solo3.total_asteroids_destroyed = 52
        alice_solo3.total_time_seconds = 210
        alice_solo3.started_at = datetime.now(timezone.utc) - timedelta(hours=8)
        alice_solo3.ended_at = datetime.now(timezone.utc) - timedelta(hours=8, minutes=3, seconds=30)
        db.add(alice_solo3)
        
        coop1 = GameSession(game_mode="coop")
        db.add(coop1)
        db.commit()
        db.refresh(coop1)
        
        coop1_bob = GameSessionPlayer(
            session_id=coop1.id,
            player_id=1,
            score=11500,
            asteroids_destroyed=43,
            deaths=0,
            currency_earned=430,
            is_host=True,
            is_ready=True
        )
        db.add(coop1_bob)
        
        coop1_alice = GameSessionPlayer(
            session_id=coop1.id,
            player_id=2,
            score=9500,
            asteroids_destroyed=35,
            deaths=2,
            currency_earned=350,
            is_host=False,
            is_ready=True
        )
        db.add(coop1_alice)
        
        coop1.total_score = 21000
        coop1.total_asteroids_destroyed = 78
        coop1.total_time_seconds = 240
        coop1.started_at = datetime.now(timezone.utc) - timedelta(days=2, hours=6)
        coop1.ended_at = datetime.now(timezone.utc) - timedelta(days=2, hours=6, minutes=4)
        db.add(coop1)
        
        coop2 = GameSession(game_mode="coop")
        db.add(coop2)
        db.commit()
        db.refresh(coop2)
        
        coop2_alice = GameSessionPlayer(
            session_id=coop2.id,
            player_id=2,
            score=8500,
            asteroids_destroyed=31,
            deaths=1,
            currency_earned=310,
            is_host=True,
            is_ready=True
        )
        db.add(coop2_alice)
        
        coop2_bob = GameSessionPlayer(
            session_id=coop2.id,
            player_id=1,
            score=7000,
            asteroids_destroyed=25,
            deaths=2,
            currency_earned=250,
            is_host=False,
            is_ready=True
        )
        db.add(coop2_bob)
        
        coop2.total_score = 15500
        coop2.total_asteroids_destroyed = 56
        coop2.total_time_seconds = 200
        coop2.started_at = datetime.now(timezone.utc) - timedelta(hours=12)
        coop2.ended_at = datetime.now(timezone.utc) - timedelta(hours=12, minutes=3)
        db.add(coop2)
        
        db.commit()

        print("Database Initialized")

@cli.command()
def test():
    print("Testing the cli")


if __name__ == "__main__":
    cli()