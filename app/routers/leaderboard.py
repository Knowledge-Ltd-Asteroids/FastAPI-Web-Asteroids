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


@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard_view(
    request: Request,
    user: AuthDep,
    db:SessionDep,
    filter: str="solo_scores"
):
    rankings = []
    title = ""

    if filter == "solo_scores":
        rankings = db.exec(select(PlayerProfile).where(PlayerProfile.active==True)
                           .order_by(PlayerProfile.highest_solo_score.desc()).limit(100)).all()
        lb_title = "HIGHEST SOLO SCORES"
    elif filter == "coop_scores":
        rankings = db.exec(select(PlayerProfile).where(PlayerProfile.active==True)
                           .order_by(PlayerProfile.highest_coop_score.desc()).limit(100)).all()
        lb_title = "HIGHEST CO-OP SCORES"
    elif filter == "asteroids_destroyed":
        rankings = db.exec(select(PlayerProfile).where(PlayerProfile.active==True)
                           .order_by(PlayerProfile.asteroids_destroyed.desc()).limit(100)).all()
        lb_title = "TOTAL ASTEROIDS DESTROYED"

    return templates.TemplateResponse(
        request=request, 
        name="leaderboard.html",
        context={
            "user": user,
            "rankings": rankings,
            "title": lb_title,
            "filter": filter 
        }
    )