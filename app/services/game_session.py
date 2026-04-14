import asyncio
import random
import uuid
import math
from typing import Dict, List, Optional, Callable
from datetime import datetime, timezone
from app.services.physics import circle_collide, circle_triangle_collision, wrap_position
from sqlmodel import select
from app.models import GameSession, GameSessionPlayer, PlayerProfile
from app.database import get_session


class AsteroidGameSession:
    TICK_RATE = 40
    TICK_INTERVAL = 1 / TICK_RATE
    ASTEROID_SPAWN_INTERVAL = 3000

    def __init__(self, session_id: str, mode: str = "solo", canvas_width: int = 1280, canvas_height: int = 720):
        self.session_id = session_id
        self.mode = mode
        self.is_active = False

        self.game_start_time: Optional[datetime] = None
        self.total_time_seconds: int = 0

        self.CANVAS_WIDTH = canvas_width
        self.CANVAS_HEIGHT = canvas_height

        self.asteroids: List[Dict] = []
        self.players: Dict[str, Dict] = {}
        self._player_db_ids: Dict[str, int] = {}  
        self.last_spawn_time = 0
        self.difficulty = 1

        self.broadcast_callback: Optional[Callable] = None
        self.task: Optional[asyncio.Task] = None
        self._session_saved = False


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
            "asteroids_destroyed": 0,
        }

    def remove_player(self, player_id: str) -> None:
        if player_id in self.players:
            del self.players[player_id]

    def register_player_db_id(self, ws_player_id: str, db_player_id: int) -> None:

        self._player_db_ids[ws_player_id] = db_player_id

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

    def add_projectile(self, player_id: str, projectile_data: Dict) -> None:
        if player_id not in self.players:
            return

        player = self.players[player_id]
        projectile = {
            "id": str(uuid.uuid4()),
            "position": projectile_data.get("position", {"x": 0, "y": 0}).copy(),
            "velocity": projectile_data.get("velocity", {"x": 0, "y": 0}).copy(),
            "radius": 5,
        }
        player["projectiles"].append(projectile)

    def update_difficulty(self, difficulty: float, spawn_interval: float) -> None:
        self.difficulty = difficulty
        self.ASTEROID_SPAWN_INTERVAL = spawn_interval
        print(f"Difficulty updated: {difficulty} | Spawn Interval: {spawn_interval}ms")

    def spawn_asteroids(self, current_time_ms: float) -> None:
        if current_time_ms - self.last_spawn_time < self.ASTEROID_SPAWN_INTERVAL:
            return

        self.last_spawn_time = current_time_ms
        spawn_count = math.floor(self.difficulty) + 2

        for _ in range(spawn_count):
            edge = random.randint(0, 3)
            radius = random.uniform(30, 50)
            speed = min(random.uniform(2, 5) * self.difficulty, 12)

            if edge == 0:
                x, y = -radius, random.uniform(0, self.CANVAS_HEIGHT)
                vx, vy = speed, random.uniform(-speed, speed)
            elif edge == 1:
                x, y = random.uniform(0, self.CANVAS_WIDTH), self.CANVAS_HEIGHT + radius
                vx, vy = random.uniform(-speed, speed), -speed
            elif edge == 2:
                x, y = self.CANVAS_WIDTH + radius, random.uniform(0, self.CANVAS_HEIGHT)
                vx, vy = -speed, random.uniform(-speed, speed)
            else:
                x, y = random.uniform(0, self.CANVAS_WIDTH), -radius
                vx, vy = random.uniform(-speed, speed), speed

            self.asteroids.append({
                "id": str(uuid.uuid4()),
                "position": {"x": x, "y": y},
                "velocity": {"x": vx, "y": vy},
                "radius": radius,
            })

    def update_asteroids(self) -> None:
        self.asteroids = [
        asteroid for asteroid in self.asteroids
        if not (
            asteroid["position"]["x"] + asteroid["radius"] < 0 or
            asteroid["position"]["x"] - asteroid["radius"] > self.CANVAS_WIDTH or
            asteroid["position"]["y"] + asteroid["radius"] < 0 or
            asteroid["position"]["y"] - asteroid["radius"] > self.CANVAS_HEIGHT
        )
    ]
        for asteroid in self.asteroids:
            asteroid["position"]["x"] += asteroid["velocity"]["x"]
            asteroid["position"]["y"] += asteroid["velocity"]["y"]

    def update_projectiles(self) -> None:
        for player_id, player in self.players.items():
            player["projectiles"] = [
                proj for proj in player["projectiles"]
                if not (
                    proj["position"]["x"] + proj["radius"] < 0 or
                    proj["position"]["x"] - proj["radius"] > self.CANVAS_WIDTH or
                    proj["position"]["y"] + proj["radius"] < 0 or
                    proj["position"]["y"] - proj["radius"] > self.CANVAS_HEIGHT
                )
            ]
            for projectile in player["projectiles"]:
                projectile["position"]["x"] += projectile["velocity"]["x"]
                projectile["position"]["y"] += projectile["velocity"]["y"]

    def check_collisions(self) -> List[Dict]:
        collision_events = []
        asteroids_to_remove = set()
        projectiles_to_remove = {}

        for player_id, player in self.players.items():
            projectiles_to_remove[player_id] = set()

            for proj_idx, projectile in enumerate(player["projectiles"]):
                for ast_idx, asteroid in enumerate(self.asteroids):
                    if ast_idx in asteroids_to_remove:
                        continue

                    if circle_collide(projectile, asteroid):
                        score_gained = int(100 * (50 / asteroid["radius"]))

                        player["score"] += score_gained
                        player["asteroids_destroyed"] += 1

                        collision_events.append({
                            "type": "asteroid_destroyed",
                            "player_id": player_id,
                            "asteroid_id": asteroid["id"],
                            "score_gained": score_gained,
                            "total_score": player["score"],
                        })

                        if asteroid["radius"] > 30:
                            new_radius = asteroid["radius"] / 2
                            random_angle = random.uniform(0, 2 * math.pi)
                            player_pos = player["position"]
                            asteroid_pos = asteroid["position"]
                            angle_to_ship = math.atan2(
                                player_pos["y"] - asteroid_pos["y"],
                                player_pos["x"] - asteroid_pos["x"],
                            )
                            self.asteroids.append({
                                "id": str(uuid.uuid4()),
                                "position": {"x": asteroid_pos["x"], "y": asteroid_pos["y"]},
                                "velocity": {"x": math.cos(angle_to_ship) * 2, "y": math.sin(angle_to_ship) * 2},
                                "radius": new_radius,
                                })

                            self.asteroids.append({
                                "id": str(uuid.uuid4()),
                                "position": {"x": asteroid_pos["x"], "y": asteroid_pos["y"]},
                                "velocity": {"x": math.cos(random_angle) * 2, "y": math.sin(random_angle) * 2},
                                "radius": new_radius,
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
                    "projectiles": p.get("projectiles", []),
                }
                for pid, p in self.players.items()
            },
        }


    async def save_session_to_db(self, db_session_id: int) -> None:

        if self._session_saved: 
            return               
        self._session_saved = True

        db = next(get_session())

        try:
            game_session = db.get(GameSession, db_session_id)
            if not game_session:
                return

            game_session.ended_at = datetime.now(timezone.utc)
            game_session.game_mode = self.mode

            total_score = 0
            total_asteroids = 0

            for player_data in self.players.values():
                total_score += player_data["score"]
                total_asteroids += player_data["asteroids_destroyed"]

            for ws_player_id, player_data in self.players.items():
                db_player_id = self._player_db_ids.get(ws_player_id)
                if db_player_id is None:
                    continue

                gsp = db.exec(
                    select(GameSessionPlayer)
                    .where(GameSessionPlayer.session_id == db_session_id)
                    .where(GameSessionPlayer.player_id == db_player_id)
                ).first()

                if gsp:
                    gsp.score = player_data["score"]
                    gsp.asteroids_destroyed = player_data["asteroids_destroyed"]
                    gsp.currency_earned = player_data["asteroids_destroyed"] * 10
                    db.add(gsp)

                profile = db.get(PlayerProfile, db_player_id)
                if profile:
                    profile.asteroids_destroyed += player_data["asteroids_destroyed"]
                    profile.currency += player_data["asteroids_destroyed"] * 10
                    profile.last_played = datetime.now(timezone.utc)
                    if self.game_start_time:
                        elapsed = datetime.now(timezone.utc) - self.game_start_time
                        session_seconds = int(elapsed.total_seconds())
                        profile.total_seconds_played += session_seconds

                    if self.mode == "solo":
                        profile.solo_games_played += 1
                        if player_data["score"] > profile.highest_solo_score:
                            profile.highest_solo_score = player_data["score"]
                    else:
                        profile.coop_games_played += 1
                        if total_score > profile.highest_coop_score:
                            profile.highest_coop_score = total_score

                    db.add(profile)

            game_session.total_score = total_score
            game_session.total_asteroids_destroyed = total_asteroids
            db.add(game_session)
            db.commit()

        except Exception as e:
            db.rollback()
            raise e

        finally:
            db.close()


    async def start(self) -> None:
        self.is_active = True
        self.game_start_time = datetime.now(timezone.utc)
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
            self.update_projectiles()

            collision_events = self.check_collisions()

            world_state = self.get_world_state()
            world_state["collisions"] = collision_events

            if self.broadcast_callback:
                await self.broadcast_callback(world_state)

            current_time_ms += self.TICK_INTERVAL * 1000
            await asyncio.sleep(self.TICK_INTERVAL)

    def stop(self) -> None:
        if self.game_start_time:
            elapsed = datetime.now(timezone.utc) - self.game_start_time
            self.total_time_seconds = int(elapsed.total_seconds())
        self.is_active = False
        if self.task:
            self.task.cancel()