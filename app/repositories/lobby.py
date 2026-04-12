from sqlmodel import Session, select
from app.models.lobby import Lobby


class LobbyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, lobby: Lobby) -> Lobby:
        self.db.add(lobby)
        self.db.commit()
        self.db.refresh(lobby)
        return lobby

    def get_by_invite_code(self, invite_code: str) -> Lobby | None:
        statement = select(Lobby).where(Lobby.invite_code == invite_code)
        return self.db.exec(statement).first()

    def get_by_id(self, lobby_id: int) -> Lobby | None:
        return self.db.get(Lobby, lobby_id)

    def get_user_lobbies(self, user_id: int, status: str = None) -> list[Lobby]:
        statement = select(Lobby).where(
            (Lobby.creator_id == user_id) | (Lobby.invited_user_id == user_id)
        )
        
        if status:
            statement = statement.where(Lobby.status == status)
        
        return self.db.exec(statement).all()

    def get_pending_invites(self, user_id: int) -> list[Lobby]:
        statement = select(Lobby).where(
            (Lobby.invited_user_id == user_id) & (Lobby.status == "waiting")
        )
        return self.db.exec(statement).all()

    def update(self, lobby: Lobby) -> Lobby:
        self.db.add(lobby)
        self.db.commit()
        self.db.refresh(lobby)
        return lobby

    def delete(self, lobby_id: int) -> None:
        lobby = self.get_by_id(lobby_id)
        if lobby:
            self.db.delete(lobby)
            self.db.commit()
