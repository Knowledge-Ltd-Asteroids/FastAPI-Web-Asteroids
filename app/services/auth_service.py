from app.repositories.user import UserRepository
from app.utilities.security import encrypt_password, verify_password, create_access_token
from app.schemas.user import RegularUserCreate
from typing import Optional
from app.models import *
from app.dependencies import SessionDep
from sqlmodel import select

class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        user = self.user_repo.get_by_username(username)
        if not user or not verify_password(plaintext_password=password, encrypted_password=user.password):
            return None
        access_token = create_access_token(data={"sub": f"{user.id}", "role": user.role})
        return access_token

    def register_user(self, username: str, email: str, password: str, db: SessionDep):
        new_user = RegularUserCreate(
            username=username, 
            email=email, 
            password=encrypt_password(password)
        )
        user = self.user_repo.create(new_user)

        profile = PlayerProfile(
            user_id=user.id,
            currency=0,
            highest_solo_score=0,
            highest_coop_score=0,
            solo_games_played=0,
            coop_games_played=0,
            asteroids_destroyed=0,
            total_seconds_played=0
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        default_ship = db.exec(select(CosmeticShip).where(CosmeticShip.is_default == True)).first()
        
        if default_ship:
            player_ship = OwnedShip(
                player_id=profile.id,
                cosmetic_ship_id=default_ship.id,
                equipped=True
            )
            db.add(player_ship)
            db.commit()
        
        return user

    
        
