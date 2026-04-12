from fastapi import HTTPException, status
from datetime import datetime, timezone
from pydantic import BaseModel

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.models.lobby import Lobby, LobbyResponse
from app.models.user import User
from app.repositories.lobby import LobbyRepository
from app.repositories.user import UserRepository
from . import api_router


class CreateLobbyRequest(BaseModel):
    """Request to create a new lobby"""
    pass


class InvitePlayerRequest(BaseModel):
    """Request to invite a player to lobby"""
    invited_username: str


class AcceptInviteRequest(BaseModel):
    """Request to accept invite"""
    invite_code: str


class LobbyDetailResponse(BaseModel):
    """Detailed lobby response"""
    id: int
    invite_code: str
    creator: dict
    invited_user: dict | None
    status: str
    created_at: datetime
    started_at: datetime | None


@api_router.post("/lobbies", response_model=LobbyResponse)
async def create_lobby(
    current_user: AuthDep,
    db: SessionDep,
    request: CreateLobbyRequest
) -> Lobby:
    """Create a new multiplayer lobby"""
    invite_code = Lobby.generate_invite_code()
    
    lobby = Lobby(
        creator_id=current_user.id,
        invite_code=invite_code,
        status="waiting"
    )
    
    lobby_repo = LobbyRepository(db)
    return lobby_repo.create(lobby)


@api_router.get("/lobbies")
async def get_my_lobbies(
    current_user: AuthDep,
    db: SessionDep,
    status: str = None
) -> list[LobbyResponse]:
    """Get lobbies where current user is creator or invited"""
    lobby_repo = LobbyRepository(db)
    lobbies = lobby_repo.get_user_lobbies(current_user.id, status=status)
    
    return [
        LobbyResponse(
            id=lobby.id,
            invite_code=lobby.invite_code,
            creator_id=lobby.creator_id,
            invited_user_id=lobby.invited_user_id,
            status=lobby.status,
            created_at=lobby.created_at
        )
        for lobby in lobbies
    ]


@api_router.get("/lobbies/pending")
async def get_pending_invites(
    current_user: AuthDep,
    db: SessionDep
) -> list[LobbyDetailResponse]:
    """Get pending invites sent to current user"""
    lobby_repo = LobbyRepository(db)
    lobbies = lobby_repo.get_pending_invites(current_user.id)
    
    return [
        LobbyDetailResponse(
            id=lobby.id,
            invite_code=lobby.invite_code,
            creator={"id": lobby.creator.id, "username": lobby.creator.username},
            invited_user={"id": lobby.invited_user.id, "username": lobby.invited_user.username} if lobby.invited_user else None,
            status=lobby.status,
            created_at=lobby.created_at,
            started_at=lobby.started_at
        )
        for lobby in lobbies
    ]


@api_router.post("/lobbies/{lobby_id}/invite")
async def invite_player(
    lobby_id: int,
    current_user: AuthDep,
    db: SessionDep,
    request: InvitePlayerRequest
) -> LobbyDetailResponse:
    """Invite a player to a lobby"""
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_id(lobby_id)
    
    if not lobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    
    # Only creator can invite
    if lobby.creator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only lobby creator can invite")
    
    # Can't invite if already has invited player
    if lobby.invited_user_id is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lobby already has an invited player")
    
    # Find player by username
    user_repo = UserRepository(db)
    invited_user = user_repo.get_by_username(request.invited_username)
    
    if not invited_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Can't invite self
    if invited_user.id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot invite yourself")
    
    # Update lobby
    lobby.invited_user_id = invited_user.id
    lobby.status = "waiting"  # Still waiting for player to accept
    lobby = lobby_repo.update(lobby)
    
    return LobbyDetailResponse(
        id=lobby.id,
        invite_code=lobby.invite_code,
        creator={"id": lobby.creator.id, "username": lobby.creator.username},
        invited_user={"id": invited_user.id, "username": invited_user.username},
        status=lobby.status,
        created_at=lobby.created_at,
        started_at=lobby.started_at
    )


@api_router.post("/lobbies/join")
async def accept_invite(
    current_user: AuthDep,
    db: SessionDep,
    request: AcceptInviteRequest
) -> LobbyDetailResponse:
    """Accept an invite and join lobby"""
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(request.invite_code)
    
    if not lobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    
    # Must be invited to this lobby
    if lobby.invited_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not invited to this lobby")
    
    # Can't accept if already playing/completed
    if lobby.status not in ["waiting", "ready"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Lobby is {lobby.status}")
    
    # Update lobby status to ready
    lobby.status = "ready"
    lobby = lobby_repo.update(lobby)
    
    return LobbyDetailResponse(
        id=lobby.id,
        invite_code=lobby.invite_code,
        creator={"id": lobby.creator.id, "username": lobby.creator.username},
        invited_user={"id": current_user.id, "username": current_user.username},
        status=lobby.status,
        created_at=lobby.created_at,
        started_at=lobby.started_at
    )


@api_router.post("/lobbies/{lobby_id}/decline")
async def decline_invite(
    lobby_id: int,
    current_user: AuthDep,
    db: SessionDep
) -> dict:
    """Decline an invite to a lobby"""
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_id(lobby_id)
    
    if not lobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    
    # Must be invited to this lobby
    if lobby.invited_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not invited to this lobby")
    
    # Delete the lobby
    lobby_repo.delete(lobby_id)
    
    return {"message": "Invite declined"}


@api_router.get("/lobbies/{invite_code}")
async def get_lobby_by_code(
    invite_code: str,
    current_user: AuthDep,
    db: SessionDep
) -> LobbyDetailResponse:
    """Get lobby by invite code"""
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(invite_code)
    
    if not lobby:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lobby not found")
    
    # User must be part of this lobby
    if lobby.creator_id != current_user.id and lobby.invited_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return LobbyDetailResponse(
        id=lobby.id,
        invite_code=lobby.invite_code,
        creator={"id": lobby.creator.id, "username": lobby.creator.username},
        invited_user={"id": lobby.invited_user.id, "username": lobby.invited_user.username} if lobby.invited_user else None,
        status=lobby.status,
        created_at=lobby.created_at,
        started_at=lobby.started_at
    )
