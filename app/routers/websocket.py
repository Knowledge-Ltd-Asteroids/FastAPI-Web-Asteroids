"""
WebSocket router for real-time game communication.
Handles solo and multiplayer game sessions.
"""
import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Cookie
from fastapi.exceptions import WebSocketException
import jwt
from app.services.game_session import AsteroidGameSession
from app.config import get_settings
from app.database import get_session
from app.repositories.lobby import LobbyRepository
from app.repositories.user import UserRepository

router = APIRouter(tags=["WebSocket"])

# Session storage: {session_id: AsteroidGameSession}
active_sessions = {}
# Connection storage: {session_id: [WebSocket, ...]}
active_connections = {}
# Player tracking: {session_id: {player_id: user_id}}
player_user_mapping = {}
# Player info tracking: {session_id: {player_id: {username, user_id}}}
player_info = {}


async def get_user_from_websocket(websocket: WebSocket) -> dict | None:
    """Extract user from WebSocket cookies/token."""
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
    """Broadcast world state to all players in a session."""
    if session_id not in active_connections:
        return
    
    disconnected = []
    for websocket in active_connections[session_id]:
        try:
            await websocket.send_json(message)
        except Exception:
            disconnected.append(websocket)
    
    # Remove disconnected clients
    for ws in disconnected:
        active_connections[session_id].remove(ws)


async def game_broadcaster(session_id: str) -> None:
    """
    Broadcasts game state from session to all connected clients.
    This callback is called by the game engine every tick.
    """
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
    """
    WebSocket endpoint for solo game.
    Each session_id creates a new isolated game instance.
    """
    await websocket.accept()
    
    # Receive initial message with canvas dimensions
    init_data = await websocket.receive_text()
    init_message = json.loads(init_data)
    
    canvas_width = init_message.get("canvas_width", 1280)
    canvas_height = init_message.get("canvas_height", 720)
    
    # Create or get session
    if session_id not in active_sessions:
        session = AsteroidGameSession(session_id, mode="solo", canvas_width=canvas_width, canvas_height=canvas_height)
        active_sessions[session_id] = session
        active_connections[session_id] = []
        
        # Register broadcast callback
        async def on_tick(world_state):
            await broadcast_to_room(session_id, {
                "type": "game_state",
                "data": world_state,
            })
        
        session.broadcast_callback = on_tick
        
        # Start game loop in background
        game_task = asyncio.create_task(session.start())
    else:
        session = active_sessions[session_id]
    
    # Track this connection
    active_connections[session_id].append(websocket)
    
    # Generate player_id for this connection
    player_id = f"solo_player_{len(active_connections[session_id])}"
    session.add_player(player_id)
    
    # Send connection confirmation
    await websocket.send_json({
        "type": "connection",
        "player_id": player_id,
        "canvas_width": session.CANVAS_WIDTH,
        "canvas_height": session.CANVAS_HEIGHT,
    })
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle client input
            if message["type"] == "player_update":
                session.update_player_state(player_id, message["data"])
            
            elif message["type"] == "game_over":
                # Client signaled game over
                pass
    
    except WebSocketDisconnect:
        # Clean up on disconnect
        active_connections[session_id].remove(websocket)
        session.remove_player(player_id)
        
        # If no more players, stop session
        if len(session.players) == 0:
            session.stop()
            if session_id in active_sessions:
                del active_sessions[session_id]
            if session_id in active_connections:
                del active_connections[session_id]
    
    except Exception as e:
        print(f"WebSocket error in {session_id}: {e}")
        await websocket.close(code=status.WS_1011_SERVER_ERROR)


@router.websocket("/ws/multiplayer/{invite_code}")
async def websocket_multiplayer_endpoint(websocket: WebSocket, invite_code: str):
    """
    WebSocket endpoint for multiplayer 2-player game.
    Requires authentication via access_token cookie.
    Invite code must correspond to a valid, ready lobby.
    """
    await websocket.accept()
    
    # Authenticate the user
    user_data = await get_user_from_websocket(websocket)
    if not user_data:
        await websocket.send_json({"type": "error", "message": "Unauthorized"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    user_id = user_data["user_id"]
    
    # Get database session and verify lobby
    db = next(get_session())
    lobby_repo = LobbyRepository(db)
    lobby = lobby_repo.get_by_invite_code(invite_code)
    
    if not lobby:
        await websocket.send_json({"type": "error", "message": "Lobby not found"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify user is creator or invited player
    if user_id != lobby.creator_id and user_id != lobby.invited_user_id:
        await websocket.send_json({"type": "error", "message": "Access denied"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    # Verify lobby status is acceptable
    # - Creator can join when status is "waiting" (and will wait for player)
    # - Creator can join when status is "ready" (second player joined)
    # - Creator can join when status is "playing" (game is in progress)
    # - Invited player can only join when status is "ready" or "playing"
    if user_id == lobby.creator_id:
        # Creator can join in any active state
        if lobby.status not in ["waiting", "ready", "playing"]:
            await websocket.send_json({"type": "error", "message": f"Lobby is {lobby.status}"})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    else:
        # Invited player can join when ready or game is already playing
        if lobby.status not in ["ready", "playing"]:
            await websocket.send_json({"type": "error", "message": f"Lobby is {lobby.status}, please wait..."})
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    
    # Receive initial message with canvas dimensions
    try:
        init_data = await websocket.receive_text()
        init_message = json.loads(init_data)
    except Exception:
        await websocket.close(code=status.WS_1011_SERVER_ERROR)
        return
    
    canvas_width = init_message.get("canvas_width", 1280)
    canvas_height = init_message.get("canvas_height", 720)
    
    # Use invite_code as session identifier
    session_id = f"mp_{invite_code}"
    
    # Create or get session
    if session_id not in active_sessions:
        session = AsteroidGameSession(session_id, mode="multiplayer", canvas_width=canvas_width, canvas_height=canvas_height)
        active_sessions[session_id] = session
        active_connections[session_id] = []
        player_user_mapping[session_id] = {}
        
        # Register broadcast callback
        async def on_tick(world_state):
            await broadcast_to_room(session_id, {
                "type": "game_state",
                "data": world_state,
            })
        
        session.broadcast_callback = on_tick
        
        # Start game loop in background
        asyncio.create_task(session.start())
        
        # Update lobby to playing
        lobby.status = "playing"
        from datetime import datetime, timezone
        lobby.started_at = datetime.now(timezone.utc)
        lobby_repo.update(lobby)
    else:
        session = active_sessions[session_id]
    
    # Track this connection
    active_connections[session_id].append(websocket)
    
    # Generate player_id based on which player this is (creator or invited)
    if user_id == lobby.creator_id:
        player_id = f"player_creator_{user_id}"
    else:
        player_id = f"player_invited_{user_id}"
    
    # Track user_id mapping and player info
    player_user_mapping[session_id][player_id] = user_id
    
    # Get user info for client
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    username = user.username if user else "Unknown"
    
    # Track player info for opponent lookups
    if session_id not in player_info:
        player_info[session_id] = {}
    player_info[session_id][player_id] = {
        "username": username,
        "user_id": user_id
    }
    
    session.add_player(player_id)
    
    # Send connection confirmation
    try:
        await websocket.send_json({
            "type": "connection",
            "player_id": player_id,
            "user_id": user_id,
            "username": username,
            "canvas_width": session.CANVAS_WIDTH,
            "canvas_height": session.CANVAS_HEIGHT,
            "mode": "multiplayer",
        })
        print(f"[WS] Sent connection confirmation to {player_id}")
    except Exception as e:
        print(f"[WS] Failed to send connection confirmation: {e}")
        await websocket.close(code=status.WS_1011_SERVER_ERROR)
        return
    
    # Notify all other players about this new player
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
            
            # Handle client input
            if message["type"] == "player_update":
                session.update_player_state(player_id, message["data"])
            
            elif message["type"] == "game_over":
                # Client signaled game over
                pass
    
    except WebSocketDisconnect:
        # Clean up on disconnect
        if session_id in active_connections and websocket in active_connections[session_id]:
            active_connections[session_id].remove(websocket)
        
        if session_id in active_sessions:
            session.remove_player(player_id)
            
            # Clean up player info
            if session_id in player_info and player_id in player_info[session_id]:
                del player_info[session_id][player_id]
            
            # If no more players, stop session and update lobby
            if len(session.players) == 0:
                session.stop()
                del active_sessions[session_id]
                del active_connections[session_id]
                del player_user_mapping[session_id]
                if session_id in player_info:
                    del player_info[session_id]
                
                # Update lobby to completed
                lobby.status = "completed"
                from datetime import datetime, timezone
                lobby.ended_at = datetime.now(timezone.utc)
                lobby_repo.update(lobby)
    
    except Exception as e:
        print(f"WebSocket error in {session_id}: {e}")
        await websocket.close(code=status.WS_1011_SERVER_ERROR)
