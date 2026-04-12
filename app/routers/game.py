from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Request
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.models.lobby import Lobby
from app.repositories.lobby import LobbyRepository
from . import router, templates

@router.get("/app/play/solo", response_class=HTMLResponse)
async def solo_game_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="game.html",
    )

@router.get("/app/play/multiplayer/{invite_code}", response_class=HTMLResponse)
async def multiplayer_game_view(
    request: Request,
    invite_code: str,
    current_user: AuthDep,
    db: SessionDep
):
    """Load multiplayer game with lobby verification"""
    from app.repositories.lobby import LobbyRepository
    
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(invite_code)
    
    if not lobby:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=404
        )
    
    # Verify user is part of this lobby
    if current_user.id != lobby.creator_id and current_user.id != lobby.invited_user_id:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=403
        )
    
    # Pass invite_code as template variable
    return templates.TemplateResponse(
        request=request,
        name="game_multiplayer.html",
        context={"invite_code": invite_code}
    )

@router.get("/app/play/coop", response_class=HTMLResponse)
async def coop_game_view(
    request: Request,
    current_user: AuthDep,
    db: SessionDep
):
    """Show co-op lobby selection: create or join"""
    return templates.TemplateResponse(
        request=request,
        name="coop_select.html",
        context={"username": current_user.username}
    )

@router.post("/app/play/coop/create", response_class=HTMLResponse)
async def create_coop_lobby(
    request: Request,
    current_user: AuthDep,
    db: SessionDep
):
    """Create a new co-op lobby and redirect to waiting room"""
    # Create a new lobby for co-op gameplay
    invite_code = Lobby.generate_invite_code()
    
    lobby = Lobby(
        creator_id=current_user.id,
        invite_code=invite_code,
        status="waiting"
    )
    
    lobby_repo = LobbyRepository(db)
    lobby_repo.create(lobby)
    
    # Redirect to co-op waiting page with invite code
    return RedirectResponse(
        url=f"/app/play/coop/lobby/{invite_code}",
        status_code=303
    )

@router.get("/app/play/coop/lobby/{invite_code}", response_class=HTMLResponse)
async def coop_lobby_view(
    request: Request,
    invite_code: str,
    current_user: AuthDep,
    db: SessionDep
):
    """Show co-op lobby waiting room with invite code"""
    from app.repositories.lobby import LobbyRepository
    
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(invite_code)
    
    if not lobby:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=404
        )
    
    # Verify user is part of this lobby (creator or invited player)
    if current_user.id != lobby.creator_id and current_user.id != lobby.invited_user_id:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=403
        )
    
    # Pass lobby info to template
    return templates.TemplateResponse(
        request=request,
        name="coop_lobby.html",
        context={
            "invite_code": invite_code,
            "username": current_user.username
        }
    )

@router.post("/app/play/coop/join")
async def join_coop_lobby(
    request: Request,
    current_user: AuthDep,
    db: SessionDep
):
    """Join an existing co-op lobby by invite code"""
    from app.repositories.lobby import LobbyRepository
    
    # Get invite code from form data
    form_data = await request.form()
    invite_code = form_data.get("invite_code", "").strip().upper()
    
    if not invite_code:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=400
        )
    
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(invite_code)
    
    if not lobby:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=404
        )
    
    # Check if lobby is still waiting for players
    if lobby.invited_user_id is not None:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=400,
            context={"message": "This lobby is already full or game has started"}
        )
    
    # Check if user is trying to join their own lobby
    if current_user.id == lobby.creator_id:
        return templates.TemplateResponse(
            request=request,
            name="401.html",
            status_code=400,
            context={"message": "You cannot join your own lobby"}
        )
    
    # Update lobby with invited player
    lobby.invited_user_id = current_user.id
    lobby.status = "ready"
    lobby_repo.update(lobby)
    
    # Redirect to multiplayer game
    from fastapi.responses import RedirectResponse
    return RedirectResponse(
        url=f"/app/play/multiplayer/{invite_code}",
        status_code=303
    )