from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import GuestAuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates

@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: GuestAuthDep,
    db: SessionDep
):
    equipped_ship = None
    if user and user.profile and user.profile.ships:
        for owned in user.profile.ships:
            if owned.equipped:
                equipped_ship = owned.cosmetic_ship
                break
    
    return templates.TemplateResponse(
        request=request,
        name="app.html",
        context={
            "user": user,
            "equipped_ship": equipped_ship
        }
    )