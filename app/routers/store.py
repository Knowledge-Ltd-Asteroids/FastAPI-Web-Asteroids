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
    db: SessionDep
):
    all_ships = db.exec(select(CosmeticShip)).all()
    
    owned_ship_ids = [owned.cosmetic_ship_id for owned in user.profile.ships]

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
    ship_selected = db.exec(
        select(CosmeticShip).where(CosmeticShip.id == ship_id)
    ).one_or_none()

    # Could not find ship
    if not ship_selected:
        flash(request, "Could not find this ship!", "danger")
        return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)

    # Ship already owned
    owned_ship_ids = [owned.cosmetic_ship_id for owned in user.profile.ships]
    if ship_id in owned_ship_ids:
        flash(request, "You already own this ship!", "danger")
        return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    # Insufficient funds
    if user.profile.currency < ship_selected.price:
        flash(request, "Insufficient credits", "danger")
        return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    user.profile.currency -= ship_selected.price

    for owned in user.profile.ships:
        owned.equipped = False
    
    player_ship = OwnedShip(
        cosmetic_ship_id = ship_selected.id,
        player_id = user.profile.id,
        equipped = True
    )

    db.add(player_ship)
    db.commit()
    flash(request, f"{ship_selected.name} successfully bought and equipped!", "success")
    return RedirectResponse(url=request.url_for("store_view"), status_code=status.HTTP_303_SEE_OTHER)