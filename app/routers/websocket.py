import asyncio
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.services.game_session import AsteroidGameSession
from app.config import get_settings
from app.database import get_session
from app.repositories.lobby import LobbyRepository
from app.repositories.user import UserRepository
from app.models import GameSession, GameSessionPlayer, PlayerProfile
from sqlmodel import select
import jwt

router = APIRouter(tags=["WebSocket"])

active_sessions = {}
active_connections = {}
player_user_mapping = {}
player_info = {}


async def get_user_from_websocket(websocket: WebSocket) -> dict | None:
    try:
        token = websocket.cookies.get("access_token")
        if not token:
            return None
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[get_settings().jwt_algorithm])
        user_id = payload.get("sub")
        return {"user_id": int(user_id)} if user_id else None
    except Exception:
        return None


async def broadcast_to_room(session_id: str, message: dict) -> None:
    if session_id not in active_connections:
        return
    disconnected = []
    for websocket in active_connections[session_id]:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    for ws in disconnected:
        active_connections[session_id].remove(ws)

async def game_broadcaster(session_id: str) -> None:
    if session_id not in active_sessions:
        return
    
    session = active_sessions[session_id]
    state = session.get_world_state()
    
    await broadcast_to_room(session_id, {
        "type": "game_state",
        "data": state,
    })


@router.websocket("/ws/solo/{session_id}")
async def websocket_solo_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    user_data = await get_user_from_websocket(websocket)

    user_data = await get_user_from_websocket(websocket)
    is_guest = False

    if not user_data:
        guest_cookie = websocket.cookies.get("guest_id")
        if guest_cookie.startswith("guest_"):
            is_guest = True
        else:
            await websocket.send_json({"type": "error", "message": "Unauthorized"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    if is_guest:
        username = "Guest"
        ship_sprite = "spaceship_thrust.png"
        db_game_session_id = None
        profile_id = None
        init_data = await websocket.receive_text()
        init_message = json.loads(init_data)
        canvas_width = init_message.get("canvas_width", 1280)
        canvas_height = init_message.get("canvas_height", 720)

    else:

        user_id = user_data["user_id"]
        db = next(get_session())

        user_repo = UserRepository(db)
        user = user_repo.get_by_id(user_id)
        username = user.username if user else "Unknown"

        profile = db.exec(
            select(PlayerProfile).where(PlayerProfile.user_id == user_id)
        ).first()
        if not profile:
            await websocket.send_json({"type": "error", "message": "Player profile not found"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        equipped_ship = None
        for owned in profile.ships:
            if owned.equipped:
                equipped_ship = owned.cosmetic_ship
                break

        ship_sprite = equipped_ship.sprite if equipped_ship else "spaceship_thrust.png"

        init_data = await websocket.receive_text()
        init_message = json.loads(init_data)
        canvas_width  = init_message.get("canvas_width",  1280)
        canvas_height = init_message.get("canvas_height", 720)

        db_game_session = GameSession(game_mode="solo")
        db.add(db_game_session)
        db.commit()
        db.refresh(db_game_session)

        gsp = GameSessionPlayer(
            session_id=db_game_session.id,
            player_id = profile.id,
            is_host = True,
            is_ready = True,
        )
        db.add(gsp)
        db.commit()

        db_game_session_id = db_game_session.id  
        profile_id = profile.id  

        db.close()

    if session_id not in active_sessions:
        game_session = AsteroidGameSession(
            session_id, mode="solo",
            canvas_width=canvas_width, canvas_height=canvas_height
        )
        active_sessions[session_id] = game_session
        active_connections[session_id] = []

        async def on_tick(world_state):
            await broadcast_to_room(session_id, {"type": "game_state", "data": world_state})

        game_session.broadcast_callback = on_tick
        asyncio.create_task(game_session.start())
    else:
        game_session = active_sessions[session_id]

    active_connections[session_id].append(websocket)

    player_id = f"solo_{uuid.uuid4().hex[:8]}"
    game_session.add_player(player_id)
    game_session.register_player_db_id(player_id, profile_id)  

    await websocket.send_json({
        "type": "connection",
        "player_id": player_id,
        "username": username,
        "canvas_width": game_session.CANVAS_WIDTH,
        "canvas_height": game_session.CANVAS_HEIGHT,
        "mode": "solo",
        "ship_sprite": ship_sprite
    })

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "player_update":
                game_session.update_player_state(player_id, message["data"])

            elif message["type"] == "shoot":
                game_session.add_projectile(player_id, message["data"])

            elif message["type"] == "difficulty_update":
                game_session.update_difficulty(
                    message["data"]["difficulty"],
                    message["data"]["spawnInterval"],
                )

            elif message["type"] == "game_over":
                break

    except WebSocketDisconnect:
        pass

    finally:

        try:
            await game_session.save_session_to_db(db_game_session_id)
        except Exception as e:
            print(f"[SOLO] Failed to save session: {e}")

        active_connections[session_id].remove(websocket)
        game_session.remove_player(player_id)

        if len(game_session.players) == 0:
            game_session.stop()
            active_sessions.pop(session_id, None)
            active_connections.pop(session_id, None)


@router.websocket("/ws/multiplayer/{invite_code}")
async def websocket_multiplayer_endpoint(websocket: WebSocket, invite_code: str):
    await websocket.accept()

    user_data = await get_user_from_websocket(websocket)
    if not user_data:
        await websocket.send_json({"type": "error", "message": "Unauthorized"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = user_data["user_id"]
    db = next(get_session())

    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(invite_code)

    if not lobby:
        await websocket.send_json({"type": "error", "message": "Lobby not found"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if user_id != lobby.creator_id and user_id != lobby.invited_user_id:
        await websocket.send_json({"type": "error", "message": "Access denied"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if user_id == lobby.creator_id:
        if lobby.status not in ["waiting", "ready", "playing"]:
            await websocket.send_json({"type": "error", "message": f"Lobby is {lobby.status}"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    else:
        if lobby.status not in ["ready", "playing"]:
            await websocket.send_json({"type": "error", "message": f"Lobby is {lobby.status}, please wait..."})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    try:
        init_data = await websocket.receive_text()
        init_message = json.loads(init_data)
    except Exception:
        await websocket.close(code=status.WS_1011_SERVER_ERROR)
        return

    canvas_width  = init_message.get("canvas_width",  1280)
    canvas_height = init_message.get("canvas_height", 720)
    session_id = f"mp_{invite_code}"

    profile = db.exec(
        select(PlayerProfile).where(PlayerProfile.user_id == user_id)
    ).first()

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    username = user.username if user else "Unknown"
    
    profile_id = profile.id if profile else None

    if session_id not in active_sessions:
        game_session = AsteroidGameSession(
            session_id, mode="multiplayer",
            canvas_width=canvas_width, canvas_height=canvas_height
        )

        active_sessions[session_id] = game_session
        active_connections[session_id] = []
        player_user_mapping[session_id] = {}
        player_info[session_id] = {}

        db_game_session = GameSession(game_mode="coop")
        db.add(db_game_session)
        db.commit()
        db.refresh(db_game_session)

        game_session._db_session_id = db_game_session.id

        async def on_tick(world_state):
            await broadcast_to_room(session_id, {"type": "game_state", "data": world_state})

        game_session.broadcast_callback = on_tick
        asyncio.create_task(game_session.start())

        lobby.status = "playing"
        lobby.started_at = datetime.now(timezone.utc)
        lobby_repo.update(lobby)
    else:
        game_session = active_sessions[session_id]

    db_session_id = game_session._db_session_id

    existing_gsp = db.exec(
        select(GameSessionPlayer)
        .where(GameSessionPlayer.session_id == db_session_id)
        .where(GameSessionPlayer.player_id == profile.id)
    ).first()

    if not existing_gsp and profile:
        is_host = (user_id == lobby.creator_id)
        gsp = GameSessionPlayer(
            session_id=db_session_id,
            player_id=profile.id,
            is_host=is_host,
            is_ready=True,
        )
        db.add(gsp)
        db.commit()

    active_connections[session_id].append(websocket)

    if user_id == lobby.creator_id:
        player_id = f"player_creator_{user_id}"
    else:
        player_id = f"player_invited_{user_id}"


    player_user_mapping[session_id][player_id] = user_id
    
    equipped_ship = None
    for owned in profile.ships:
        if owned.equipped:
            equipped_ship = owned.cosmetic_ship
            break
    ship_sprite = equipped_ship.sprite if equipped_ship else "spaceship_thrust.png"
    
    player_info[session_id][player_id] = {
        "username": username,
        "user_id": user_id,
        "ship_sprite": ship_sprite
    }

    game_session.add_player(player_id)
    if profile:
        game_session.register_player_db_id(player_id, profile_id)

    await websocket.send_json({
        "type": "connection",
        "player_id": player_id,
        "user_id": user_id,
        "username": username,
        "canvas_width": game_session.CANVAS_WIDTH,
        "canvas_height": game_session.CANVAS_HEIGHT,
        "mode": "multiplayer",
        "ship_sprite": ship_sprite
    })

    other_players_info = {}
    for pid, pinfo in player_info[session_id].items():
        if pid != player_id:
            other_players_info[pid] = pinfo
    
    if other_players_info:
        try:
            await broadcast_to_room(session_id, {
                "type": "player_joined",
                "player_id": player_id,
                "username": username,
                "other_players": other_players_info,
            })
            print(f"[WS] Notified other players about {player_id}")
        except Exception as e:
            print(f"[WS] Failed to notify other players: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "player_update":
                game_session.update_player_state(player_id, message["data"])

            elif message["type"] == "shoot":
                game_session.add_projectile(player_id, message["data"])

            elif message["type"] == "difficulty_update":
                game_session.update_difficulty(
                    message["data"]["difficulty"],
                    message["data"]["spawnInterval"],
                )

            elif message["type"] == "game_over":
                break

    except WebSocketDisconnect:
        pass

    finally:
        active_connections[session_id].remove(websocket)
        game_session.remove_player(player_id)
        player_info[session_id].pop(player_id, None)

        if len(game_session.players) == 0:
            game_session.stop()

            try:
                await game_session.save_session_to_db(db_session_id, db)
            except Exception as e:
                print(f"[MP] Failed to save session: {e}")

            active_sessions.pop(session_id, None)
            active_connections.pop(session_id, None)
            player_user_mapping.pop(session_id, None)
            player_info.pop(session_id, None)

            lobby.status = "completed"
            lobby.ended_at = datetime.now(timezone.utc)
            lobby_repo.update(lobby)
        
        db.close()
