from fastapi import Request, Query
from fastapi.responses import HTMLResponse
from app.dependencies.session import SessionDep
from app.dependencies.auth import AdminDep
from . import router, templates
from sqlmodel import select, func
from app.models import *
from repositories import UserRepository


@router.get("/admin", response_class=HTMLResponse)
def admin_home_view(
    request: Request,
    db: SessionDep,
    user: AdminDep,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    q: str = Query(default=''),
    sort: str = Query(default='newest')
):
    #pagination and search query
    user_repo = UserRepository(db)
    users, pagination = user_repo.search_users(query=q, page=page, limit=limit, sort=sort)

    user_ids = [user.id for user in users]
    
    #get all user profiles
    profiles = {}
    if user_ids:
        profile_results = db.exec(select(PlayerProfile).where(PlayerProfile.user_id.in_(user_ids))
                                  .where(PlayerProfile.active == True)).all()
        profiles = {profile.user_id: profile for profile in profile_results}
        
        profile_ids = [profile.id for profile in profile_results]
        
        #get all counts of ships
        ship_counts = {}
        if profile_ids:
            ship_results = db.exec(select(OwnedShip.player_id, func.count())
                            .where(OwnedShip.player_id.in_(profile_ids))
                            .group_by(OwnedShip.player_id)).all()
            ship_counts = {player_id: count for player_id, count in ship_results}
        
        #get all total game sessions
        game_session_counts = {}
        if profile_ids:
            game_results = db.exec(
                select(GameSessionPlayer.player_id, func.count())
                .where(GameSessionPlayer.player_id.in_(profile_ids))
                .group_by(GameSessionPlayer.player_id)
            ).all()
            game_session_counts = {player_id: count for player_id, count in game_results}
    else:
        ship_counts = {}
        game_session_counts = {}
    
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={
            "user": user,
            "users": users,
            "profiles": profiles,
            "ship_counts": ship_counts,
            "game_session_counts": game_session_counts,
            "pagination": pagination,
            "q": q,
            "sort": sort,
            "total_users": pagination.total_count
        }
    )