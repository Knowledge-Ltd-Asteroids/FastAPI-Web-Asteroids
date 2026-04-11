from fastapi.responses import HTMLResponse
from fastapi import Request
from . import router, templates

@router.get("/app/play/solo", response_class=HTMLResponse)
async def solo_game_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="game.html",
    )