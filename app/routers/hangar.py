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
    return templates.TemplateResponse(
        request=request, 
        name="hangar.html",
        context={
            "user": user,
        }
    )