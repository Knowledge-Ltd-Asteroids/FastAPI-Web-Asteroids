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

@router.get("/store", response_class=HTMLResponse)
async def store_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    # get all ships and all owned ships
    all_ships = db.exec(select(Ship)).all()
    owned_ship_ids = [playership.ship_id for playership in user.profile.ships]

    #only get those not owned
    available_ships = [ship for ship in all_ships if ship.id not in owned_ship_ids]

    return templates.TemplateResponse(
        request=request, 
        name="store.html",
        context={
            "user": user,
            "ships": available_ships
        }
    )

@router.post("/store/purchase_ship", response_class=HTMLResponse)
def purchase_ship(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    ship_id: int = Form()
):
    ship_selected = db.exec(select(Ship).where(Ship.id == ship_id)).one_or_none()

    #could not find ship
    if not ship_selected:
        flash(request, "Could not find this ship!", "danger")
        return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)

    #ship already owned
    owned_ship_ids = [playership.ship_id for playership in user.profile.ships]
    if ship_id in owned_ship_ids:
        flash(request, "You already own this ship!", "danger")
        return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    #insufficient funds
    if user.profile.currency < ship_selected.price:
        flash(request, "Insufficient credits", "danger")
        return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    #update user currency and commit
    user.profile.currency -= ship_selected.price

    #unequip currently equipped ship
    for playership in user.profile.ships:
        playership.equipped = False
    
    player_ship = PlayerShip(
        ship_id = ship_selected.id,
        player_id = user.profile.id,
        equipped=True
    )

    db.add(player_ship)
    db.commit()
    flash(request, f"{ship_selected.name} successfully bought and equipped!", "success")
    return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)