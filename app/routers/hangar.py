from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.models import *
from sqlmodel import select
from app.utilities.flash import flash
from typing import Optional
from app.repositories import UserRepository


@router.get("/hangar", response_class=HTMLResponse)
async def user_hangar_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    #get all ships and IDs of owned ships
    all_ships = db.exec(select(CosmeticShip)).all()
    owned_ship_ids = [playership.cosmetic_ship_id for playership in user.profile.ships]

    #only get the owned ships
    owned_ships = [ship for ship in all_ships if ship.id in owned_ship_ids]

    #get the equipped ship to be highlighted
    equipped_ship_id = None
    for playership in user.profile.ships:
        if playership.equipped:
            equipped_ship_id = playership.cosmetic_ship_id
            break
    
    return templates.TemplateResponse(
        request=request, 
        name="hangar.html",
        context={
            "owned_ships": owned_ships,
            "user": user,
            "equipped_ship_id": equipped_ship_id
        }
    )

@router.post("/hangar/equip", response_class=HTMLResponse)
def equip_ship(
    request: Request,
    user: AuthDep,
    db:SessionDep,
    ship_id: int = Form()
):
    # check for ownership of the selected ship
    player_ship_selected = db.exec(select(OwnedShip).where
                                   (OwnedShip.cosmetic_ship_id == ship_id,
                                    OwnedShip.player_id == user.profile.id)).one_or_none()

    if not player_ship_selected:
        flash(request, "Could not find this ship!", "danger")
        return RedirectResponse(url=request.url_for("user_hangar_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    #unequip the currently equipped ship
    for playership in user.profile.ships:
        playership.equipped = False

    #equip the selected ship
    player_ship_selected.equipped = True
    db.commit()

    flash(request, f"{player_ship_selected.cosmetic_ship.name} successfully equipped!", "success")
    return RedirectResponse(url=request.url_for("user_hangar_view"), status_code=status.HTTP_303_SEE_OTHER)