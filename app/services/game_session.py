import asyncio
import random
import uuid
from typing import Dict, List, Optional, Callable
from datetime import datetime
from app.services.physics import circle_collide, circle_triangle_collision, wrap_position


class AsteroidGameSession:
    TICK_RATE = 20
    TICK_INTERVAL = 1 / TICK_RATE
    ASTEROID_SPAWN_INTERVAL = 3000
    
    def __init__(self, session_id: str, mode: str = "solo", canvas_width: int = 1280, canvas_height: int = 720):
        self.session_id = session_id
        self.mode = mode
        self.is_active = False
        
        self.CANVAS_WIDTH = canvas_width
        self.CANVAS_HEIGHT = canvas_height
        
        self.asteroids: List[Dict] = []
        self.players: Dict[str, Dict] = {}
        self.last_spawn_time = 0
        
        self.broadcast_callback: Optional[Callable] = None
        self.task: Optional[asyncio.Task] = None
    
    def add_player(self, player_id: str, initial_position: Dict = None) -> None:
        if initial_position is None:
            initial_position = {"x": self.CANVAS_WIDTH / 2, "y": self.CANVAS_HEIGHT / 2}
        
        self.players[player_id] = {
            "position": initial_position.copy(),
            "rotation": 0,
            "velocity": {"x": 0, "y": 0},
            "projectiles": [],
            "lives": 3,
            "score": 0,
        }
    
    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            del self.players[player_id]
    
    def update_player_state(self, player_id: str, state: Dict) -> None:
        if player_id not in self.players:
            return
        
        player = self.players[player_id]
        
        if "position" in state:
            player["position"] = state["position"].copy()
        if "rotation" in state:
            player["rotation"] = state["rotation"]
        if "velocity" in state:
            player["velocity"] = state["velocity"].copy()
        if "projectiles" in state:
            player["projectiles"] = state["projectiles"]
    
    def spawn_asteroids(self, current_time_ms: float) -> None:
        if current_time_ms - self.last_spawn_time < self.ASTEROID_SPAWN_INTERVAL:
            return
        
        self.last_spawn_time = current_time_ms
        
        edge = random.randint(0, 3)
        radius = random.uniform(10, 50)
        
        speed = random.uniform(1, 3)
        
        if edge == 0:
            x, y = -radius, random.uniform(0, self.CANVAS_HEIGHT)
            vx = speed
            vy = random.uniform(-speed, speed)
        elif edge == 1:
            x, y = random.uniform(0, self.CANVAS_WIDTH), self.CANVAS_HEIGHT + radius
            vx = random.uniform(-speed, speed)
            vy = -speed
        elif edge == 2:
            x, y = self.CANVAS_WIDTH + radius, random.uniform(0, self.CANVAS_HEIGHT)
            vx = -speed
            vy = random.uniform(-speed, speed)
        else:
            x, y = random.uniform(0, self.CANVAS_WIDTH), -radius
            vx = random.uniform(-speed, speed)
            vy = speed
        
        asteroid = {
            "id": str(uuid.uuid4()),
            "position": {"x": x, "y": y},
            "velocity": {"x": vx, "y": vy},
            "radius": radius,
        }
        
        self.asteroids.append(asteroid)
    
    def update_asteroids(self) -> None:
        for asteroid in self.asteroids:
            asteroid["position"]["x"] += asteroid["velocity"]["x"]
            asteroid["position"]["y"] += asteroid["velocity"]["y"]

            asteroid["position"] = wrap_position(
                asteroid["position"],
                self.CANVAS_WIDTH,
                self.CANVAS_HEIGHT,
                asteroid["radius"]
            )
    
    def check_collisions(self) -> List[Dict]:
        collision_events = []
        asteroids_to_remove = set()
        projectiles_to_remove = {}
        
        for player_id, player in self.players.items():
            projectiles_to_remove[player_id] = set()
            
            for proj_idx, projectile in enumerate(player["projectiles"]):
                for ast_idx, asteroid in enumerate(self.asteroids):
                    if circle_collide(projectile, asteroid):
                        collision_events.append({
                            "type": "asteroid_destroyed",
                            "player_id": player_id,
                            "asteroid_id": asteroid["id"],
                            "score_gained": int(100 * (50 / asteroid["radius"]))
                        })
                        asteroids_to_remove.add(ast_idx)
                        projectiles_to_remove[player_id].add(proj_idx)
                        break
        
        for player_id, player in self.players.items():
            ship_vertices = self._get_ship_vertices(player)
            
            for ast_idx, asteroid in enumerate(self.asteroids):
                if circle_triangle_collision(asteroid, ship_vertices):
                    collision_events.append({
                        "type": "ship_hit",
                        "player_id": player_id,
                        "asteroid_id": asteroid["id"],
                    })
                    player["lives"] -= 1
                    asteroids_to_remove.add(ast_idx)
        
        self.asteroids = [a for i, a in enumerate(self.asteroids) if i not in asteroids_to_remove]
        
        for player_id in projectiles_to_remove:
            self.players[player_id]["projectiles"] = [
                p for i, p in enumerate(self.players[player_id]["projectiles"])
                if i not in projectiles_to_remove[player_id]
            ]
        
        return collision_events
    
    def _get_ship_vertices(self, player: Dict) -> List[Dict]:
        pos = player["position"]
        rot = player["rotation"]
        
        cos_r = __import__("math").cos(rot)
        sin_r = __import__("math").sin(rot)
        
        return [
            {
                "x": pos["x"] + cos_r * 30 - sin_r * 0,
                "y": pos["y"] + sin_r * 30 + cos_r * 0,
            },
            {
                "x": pos["x"] + cos_r * -10 - sin_r * 10,
                "y": pos["y"] + sin_r * -10 + cos_r * 10,
            },
            {
                "x": pos["x"] + cos_r * -10 - sin_r * -10,
                "y": pos["y"] + sin_r * -10 + cos_r * -10,
            },
        ]
    
    def get_world_state(self) -> Dict:
        return {
            "asteroids": self.asteroids,
            "players": {
                pid: {
                    "position": p["position"],
                    "rotation": p["rotation"],
                    "lives": p["lives"],
                    "score": p["score"],
                }
                for pid, p in self.players.items()
            },
        }
    
    async def start(self) -> None:
        self.is_active = True
        try:
            await self._game_loop()
        except asyncio.CancelledError:
            pass
        finally:
            self.is_active = False
    
    async def _game_loop(self) -> None:
        current_time_ms = 0
        
        while self.is_active:
            self.spawn_asteroids(current_time_ms)
            self.update_asteroids()
            
            collision_events = self.check_collisions()
            
            world_state = self.get_world_state()
            world_state["collisions"] = collision_events
            
            if self.broadcast_callback:
                await self.broadcast_callback(world_state)
            
            current_time_ms += self.TICK_INTERVAL * 1000
            await asyncio.sleep(self.TICK_INTERVAL)
    
    def stop(self) -> None:
        self.is_active = False
        if self.task:
            self.task.cancel()
