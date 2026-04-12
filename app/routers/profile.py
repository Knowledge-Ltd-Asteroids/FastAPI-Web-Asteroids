from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.models import *
from sqlmodel import select, func
from app.utilities.flash import flash
from typing import Optional
from app.repositories import UserRepository


#send the profile details
@router.get("/profile", response_class=HTMLResponse)
async def user_profile_view(
    request: Request,
    user: AuthDep,
    db:SessionDep
):
    player_profile = db.exec(select(PlayerProfile).where(user.id == PlayerProfile.user_id)).one_or_none()
    if not player_profile:
        flash(request, "Player Profile NOT Found!", "danger")
        return RedirectResponse(url=request.url_for("user_home_view"), status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        request=request, 
        name="profile.html",
        context={
            "user": user,
            "profile": player_profile
        }
    )

#update a user's username
#change to put and use js in profile.html to call
@router.post("/profile_update_username")
def update_player_username(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    new_username: Optional[str] = Form(),
):
    user_repo = UserRepository(db)

    #just redirect if its the same username
    if new_username == user.username:
        flash(request, "Successfully updated username!", "success")
        return RedirectResponse(url=request.url_for("user_profile_view"), status_code=status.HTTP_303_SEE_OTHER)
   
   #username already exists
    if new_username and user_repo.get_by_username(new_username):
        flash(request, "This username is already taken!", "danger")
        return RedirectResponse(url=request.url_for("user_profile_view"), status_code = status.HTTP_303_SEE_OTHER)
    
    try:
        user_update = UserUpdate(username=new_username)
        user_repo.update_user(user.id, user_update)
        flash(request, "Successfully updated username!", "success")
    except Exception as e:
        flash(request, "Invalid username", "danger")

    return RedirectResponse(url=request.url_for("user_profile_view"), status_code=status.HTTP_303_SEE_OTHER)

#update a user's email
#change to put and use js in profile.html to call
@router.post("/profile_update_email")
def update_player_email(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    new_email: Optional[str] = Form(),
):
    user_repo = UserRepository(db)

    #just redirect if its the same email
    if new_email == user.email:
        flash(request, "Successfully updated email!", "success")
        return RedirectResponse(url=request.url_for("user_profile_view"), status_code=status.HTTP_303_SEE_OTHER)
   
   #email already exists
    if new_email and user_repo.get_by_email(new_email):
        flash(request, "This email is already registered with another account!", "danger")
        return RedirectResponse(url=request.url_for("user_profile_view"), status_code = status.HTTP_303_SEE_OTHER)
    
    try:
        user_update = UserUpdate(email=new_email)
        user_repo.update_user(user.id, user_update)
        flash(request, "Successfully updated email!", "success")
    except Exception as e:
        flash(request, "Invalid email", "danger")

    return RedirectResponse(url=request.url_for("user_profile_view"), status_code=status.HTTP_303_SEE_OTHER)

@router.delete("/profile/delete")
async def delete_profile(
    request: Request,
    user: AuthDep,
    db: SessionDep
):
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.delete(user)
        db.commit()
        request.session.clear()
        return {"message": "Your account has been permanently deleted"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while deleting your account")