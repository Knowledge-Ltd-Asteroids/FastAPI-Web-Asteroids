const canvas = document.getElementById("canvas");
const c = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

const asteroidSprites = {
    big2: new Image(),
    medium1: new Image(),
    medium2: new Image(),
    small1: new Image(),
    small2: new Image()
};

asteroidSprites.big2.src = '/static/Asteroids Asset Pack/sprites/asteroids/asteroid_big2.png';
asteroidSprites.medium1.src = '/static/Asteroids Asset Pack/sprites/asteroids/asteroid_medium1.png';
asteroidSprites.medium2.src = '/static/Asteroids Asset Pack/sprites/asteroids/asteroid_medium2.png';
asteroidSprites.small1.src = '/static/Asteroids Asset Pack/sprites/asteroids/asteroid_small1.png';
asteroidSprites.small2.src = '/static/Asteroids Asset Pack/sprites/asteroids/asteroid_small2.png';

c.fillStyle = "black";
c.fillRect(0, 0, canvas.width, canvas.height);

let gameMode = "solo";
let gameState = {
    asteroids: [],
    players: {},
    playerLives: 3,
    playerScore: 0,
};

let playerId = null;
let playerName = null;
let opponentData = null;
let opponentName = null;
let ws = null;
let isGameOver = false;

class SpaceShip {
    constructor({ position, velocity }) {
        this.position = position;
        this.velocity = velocity;
        this.rotation = 0;
    }

    draw() {
        c.save();
        c.translate(this.position.x, this.position.y);
        c.rotate(this.rotation);
        c.translate(-this.position.x, -this.position.y);

        c.beginPath();
        c.moveTo(this.position.x + 30, this.position.y);
        c.lineTo(this.position.x - 10, this.position.y - 10);
        c.lineTo(this.position.x - 10, this.position.y + 10);
        c.closePath();
        c.strokeStyle = "white";
        c.stroke();

        if (keys.w.pressed) {
            const flameLength = 15 + Math.random() * 10;
            c.beginPath();
            c.moveTo(this.position.x - 10, this.position.y - 5); // Top of Truster
            c.lineTo(this.position.x - 25, this.position.y); // Tip of Truster
            c.lineTo(this.position.x - 10, this.position.y + 5); // Bottom of Truster
            c.closePath();
            c.fillStyle = "orange";
            c.fill();
        }

        c.restore();
    }

    update() {
        this.draw();
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;

        if (this.position.x > canvas.width) { this.position.x = 0; }
        if (this.position.x < 0) { this.position.x = canvas.width; }
        if (this.position.y > canvas.height) { this.position.y = 0; }
        if (this.position.y < 0) { this.position.y = canvas.height; }
    }

    getVertices() {
        const cos = Math.cos(this.rotation);
        const sin = Math.sin(this.rotation);

        return [
            {
                x: this.position.x + cos * 30 - sin * 0,
                y: this.position.y + sin * 30 + cos * 0,
            },
            {
                x: this.position.x + cos * -10 - sin * 10,
                y: this.position.y + sin * -10 + cos * 10,
            },
            {
                x: this.position.x + cos * -10 - sin * -10,
                y: this.position.y + sin * -10 + cos * -10,
            },
        ];
    }
}

class OpponentShip {
    constructor({ position, rotation }) {
        this.position = position;
        this.rotation = rotation;
    }

    draw(color = "#E1B100") {
        c.save();
        c.translate(this.position.x, this.position.y);
        c.rotate(this.rotation);
        c.translate(-this.position.x, -this.position.y);

        c.beginPath();
        c.moveTo(this.position.x + 30, this.position.y);
        c.lineTo(this.position.x - 10, this.position.y - 10);
        c.lineTo(this.position.x - 10, this.position.y + 10);
        c.closePath();
        c.strokeStyle = color;
        c.lineWidth = 2;
        c.stroke();
        c.restore();
    }

    update(data) {
        this.position = data.position;
        this.rotation = data.rotation;
        this.draw();
    }
}

class Projectiles {
    constructor({ position, velocity }) {
        this.position = position;
        this.velocity = velocity;
        this.radius = 5;
        this.id = crypto.randomUUID();
    }

    draw() {
        c.beginPath();
        c.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2, false);
        c.closePath();
        c.fillStyle = "white";
        c.fill();
    }

    update() {
        this.draw();
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
    }
}

class Asteroid {
    constructor({ id, position, velocity, radius }) {
        this.id = id;
        this.position = position;
        this.velocity = velocity;
        this.radius = radius;
        this.rotation = Math.random() * Math.PI * 2;
        this.rotationSpeed = (Math.random() - 0.5) * 0.03;

        if (radius > 40) {
            this.sprite = asteroidSprites.big2;
        } else if (radius > 20) {
            if (Math.random() < 0.5) {
                this.sprite = asteroidSprites.medium1;
            } else {
                this.sprite = asteroidSprites.medium2;
            }
        } else {
            if (Math.random() < 0.5) {
                this.sprite = asteroidSprites.small1;
            } else {
                this.sprite = asteroidSprites.small2;
            }
        }
    }

    draw() {

        c.save();
        c.translate(this.position.x, this.position.y);
        c.rotate(this.rotation);

        const size = this.radius * 2;

        if (this.sprite && this.sprite.complete && this.sprite.naturalWidth > 0) {

            c.drawImage(this.sprite, -this.radius, -this.radius, size, size);
        }

        else {
            c.beginPath();
            c.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2, false);
            c.closePath();
            c.strokeStyle = "white";
            c.stroke();
        }
        c.restore();
    }

    update() {
        this.draw();
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
        this.rotation += this.rotationSpeed;
    }
}

function circleCollide(circle1, circle2) {
    const xDist = circle2.position.x - circle1.position.x;
    const yDist = circle2.position.y - circle1.position.y;
    const distance = Math.sqrt(Math.pow(xDist, 2) + Math.pow(yDist, 2));
    return distance <= circle1.radius + circle2.radius;
}

function isPointOnLineSegment(x, y, begin, end) {
    return (
        x >= Math.min(begin.x, end.x) &&
        x <= Math.max(begin.x, end.x) &&
        y >= Math.min(begin.y, end.y) &&
        y <= Math.max(begin.y, end.y)
    );
}

function circleTriangleCollision(circle, triangle) {
    for (let i = 0; i < 3; i++) {
        let begin = triangle[i];
        let end = triangle[(i + 1) % 3];

        let dx = end.x - begin.x;
        let dy = end.y - begin.y;
        let length = Math.sqrt(dx * dx + dy * dy);

        let t = ((circle.position.x - begin.x) * dx + (circle.position.y - begin.y) * dy) / (length * length);

        let closestX = begin.x + t * dx;
        let closestY = begin.y + t * dy;

        if (!isPointOnLineSegment(closestX, closestY, begin, end)) {
            closestX = closestX < begin.x ? begin.x : end.x;
            closestY = closestY < begin.y ? begin.y : end.y;
        }

        dx = closestX - circle.position.x;
        dy = closestY - circle.position.y;
        let distance = Math.sqrt(dx * dx + dy * dy);

        if (distance <= circle.radius) {
            return true;
        }
    }
    return false;
}

const spaceship = new SpaceShip({
    position: { x: canvas.width / 2, y: canvas.height / 2 },
    velocity: { x: 0, y: 0 },
});

const keys = {
    w: { pressed: false },
    a: { pressed: false },
    d: { pressed: false },
};

const projectiles = [];
let animationID = null;
const asteroidMap = new Map();

const Spaceship_Speed = 4;
const Rotate_Speed = 0.05;
const Projectile_Speed = 10;
const Friction = 0.95;

window.addEventListener("keydown", (event) => {
    switch (event.code) {
        case "KeyW":
            keys.w.pressed = true;
            break;
        case "KeyA":
            keys.a.pressed = true;
            break;
        case "KeyD":
            keys.d.pressed = true;
            break;
        case "Space":
            projectiles.push(
                new Projectiles({
                    position: {
                        x: spaceship.position.x + Math.cos(spaceship.rotation) * 30,
                        y: spaceship.position.y + Math.sin(spaceship.rotation) * 30,
                    },
                    velocity: {
                        x: Math.cos(spaceship.rotation) * Projectile_Speed,
                        y: Math.sin(spaceship.rotation) * Projectile_Speed,
                    },
                })
            );
            break;
    }
});

window.addEventListener("keyup", (event) => {
    switch (event.code) {
        case "KeyW":
            keys.w.pressed = false;
            break;
        case "KeyA":
            keys.a.pressed = false;
            break;
        case "KeyD":
            keys.d.pressed = false;
            break;
    }
});

function animate() {
    animationID = window.requestAnimationFrame(animate);

    c.fillStyle = "black";
    c.fillRect(0, 0, canvas.width, canvas.height);

    spaceship.update();

    if (spaceship.position.x > canvas.width) {
        spaceship.position.x = 0;
    }
    if (spaceship.position.x < 0) {
        spaceship.position.x = canvas.width;
    }
    if (spaceship.position.y > canvas.height) {
        spaceship.position.y = 0;
    }
    if (spaceship.position.y < 0) {
        spaceship.position.y = canvas.height;
    }


    for (let i = projectiles.length - 1; i >= 0; i--) {
        const projectile = projectiles[i];
        projectile.update();

        if (
            projectile.position.x + projectile.radius < 0 ||
            projectile.position.x - projectile.radius > canvas.width ||
            projectile.position.y - projectile.radius > canvas.height ||
            projectile.position.y + projectile.radius < 0
        ) {
            projectiles.splice(i, 1);
        }
    }

    for (let i = gameState.asteroids.length - 1; i >= 0; i--) {
        const asteroidData = gameState.asteroids[i];

        if (!asteroidMap.has(asteroidData.id)) {
            asteroidMap.set(asteroidData.id, new Asteroid(asteroidData));
        }

        const asteroid = asteroidMap.get(asteroidData.id);
        asteroid.position.x += (asteroidData.position.x - asteroid.position.x) * 0.5;
        asteroid.position.y += (asteroidData.position.y - asteroid.position.y) * 0.5;

        asteroid.rotation += asteroid.rotationSpeed;
        asteroid.draw();
    }

    const activeIds = new Set(gameState.asteroids.map(a => a.id));
    for (const id of asteroidMap.keys()) {
        if (!activeIds.has(id)) {
            asteroidMap.delete(id);
        }
    }

    if (gameMode === "multiplayer" && opponentData) {
        const opponent = new OpponentShip(opponentData);
        opponent.draw("#E1B100");
    }

    if (keys.w.pressed) {
        spaceship.velocity.x = Math.cos(spaceship.rotation) * Spaceship_Speed;
        spaceship.velocity.y = Math.sin(spaceship.rotation) * Spaceship_Speed;
    } else if (!keys.w.pressed) {
        spaceship.velocity.x *= Friction;
        spaceship.velocity.y *= Friction;
    }

    if (keys.a.pressed) {
        spaceship.rotation -= Rotate_Speed;
    } else if (keys.d.pressed) {
        spaceship.rotation += Rotate_Speed;
    }

    renderStats();
    sendPlayerState();
}

let difficulty = 1;
let spawnInterval = 3000;

const difficultyInterval = window.setInterval(() => {
    difficulty += 0.4;
    spawnInterval = Math.max(800, spawnInterval - 130);

    console.log(`Difficulty: ${difficulty} | Spawn Interval: ${spawnInterval}ms`);

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: "difficulty_update",
            data: {
                difficulty: difficulty,
                spawnInterval: spawnInterval,
            }
        }));
    }
}, 15000);

function renderStats() {
    if (gameMode === "solo") {
        c.fillStyle = "white";
        c.font = "20px Arial";
        c.fillText(`Lives: ${gameState.playerLives}`, 20, 30);
        c.fillText(`Score: ${gameState.playerScore}`, 20, 60);

        if (!ws || ws.readyState !== WebSocket.OPEN) {
            c.fillStyle = "red";
            c.fillText("DISCONNECTED", canvas.width - 200, 30);
        }
    } else {
        const playerIds = Object.keys(gameState.players);

        let selfData = gameState.players[playerId];
        let opponentId = playerIds.find(pid => pid !== playerId);
        let opponentPlayerData = opponentId ? gameState.players[opponentId] : null;

        if (selfData) {
            document.getElementById("p1-name").textContent = playerName || "Player 1";
            document.getElementById("p1-score").textContent = selfData.score;
            document.getElementById("p1-lives").textContent = selfData.lives;
            gameState.playerLives = selfData.lives;
            gameState.playerScore = selfData.score;
        }

        if (opponentPlayerData) {
            document.getElementById("p2-name").textContent = opponentName || "Player 2";
            document.getElementById("p2-score").textContent = opponentPlayerData.score;
            document.getElementById("p2-lives").textContent = opponentPlayerData.lives;

            opponentData = {
                position: opponentPlayerData.position,
                rotation: opponentPlayerData.rotation
            };
        }

        const statusEl = document.getElementById("connection-status");
        if (ws && ws.readyState === WebSocket.OPEN) {
            statusEl.textContent = "Connected";
            statusEl.className = "connection-status connected";
        } else {
            statusEl.textContent = "Disconnected";
            statusEl.className = "connection-status disconnected";
        }
    }
}

function initializeWebSocket() {
    const isMultiplayer = window.location.pathname.includes("/multiplayer/");
    let wsUrl;

    if (isMultiplayer) {
        const pathSegments = window.location.pathname.split("/");
        const inviteCode = pathSegments[pathSegments.length - 1];
        gameMode = "multiplayer";

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${protocol}//${window.location.host}/ws/multiplayer/${inviteCode}`;
    } else {
        const sessionId = "solo_" + Date.now();
        gameMode = "solo";

        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${protocol}//${window.location.host}/ws/solo/${sessionId}`;
    }

    console.log(`[${gameMode.toUpperCase()}] Connecting to: ${wsUrl}`);

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log(`[${gameMode.toUpperCase()}] WebSocket connected`);

        ws.send(JSON.stringify({
            canvas_width: canvas.width,
            canvas_height: canvas.height,
        }));

        animate();
    };

    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);

        if (message.type === "connection") {
            playerId = message.player_id;
            playerName = message.username || "Unknown";
            console.log(`Player ID: ${playerId} (${playerName})`);
            console.log(`Mode: ${message.mode || 'unknown'}`);
            if (message.mode === "multiplayer") {
                gameMode = "multiplayer";
            }
        }

        if (message.type === "player_joined") {
            console.log(`Player joined: ${message.username}`);

            if (message.player_id !== playerId) {
                opponentName = message.username;
                console.log(`Opponent: ${opponentName}`);
            }

            if (message.other_players) {
                for (const [pId, pInfo] of Object.entries(message.other_players)) {
                    if (pId !== playerId) {
                        opponentName = pInfo.username;
                    }
                }
            }
        }

        if (message.type === "game_state") {
            const data = message.data;

            gameState.asteroids = data.asteroids.map((ast) => ({
                id: ast.id,
                position: ast.position,
                velocity: ast.velocity,
                radius: ast.radius,
            }));

            gameState.players = {};
            for (const [pId, playerData] of Object.entries(data.players)) {
                gameState.players[pId] = {
                    position: playerData.position,
                    rotation: playerData.rotation,
                    lives: playerData.lives,
                    score: playerData.score
                };
            }

            const selfData = gameState.players[playerId];
            if (selfData) {
                gameState.playerLives = selfData.lives;
                gameState.playerScore = selfData.score;
            }

            if (data.collisions && data.collisions.length > 0) {
                data.collisions.forEach((collision) => {
                    if (collision.type === "asteroid_destroyed") {
                        console.log(`Asteroid destroyed! Score: +${collision.score_gained}`);
                        projectiles.length = 0;
                    } else if (collision.type === "ship_hit") {
                        console.log("Ship hit! Lives decreased");
                    }
                });
            }

            if (gameMode === "multiplayer") {
                const allPlayers = Object.values(gameState.players || {});
                const anyPlayerDead = allPlayers.some(p => p.lives <= 0);
                if (anyPlayerDead) {
                    console.log(`[${gameMode.toUpperCase()}] A player reached 0 lives. Game Over!`);
                    endGame();
                }
            } else {
                if (selfData && selfData.lives <= 0) {
                    console.log(`[${gameMode.toUpperCase()}] Game Over!`);
                    endGame();
                }
            }
        }
    };

    ws.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
        console.log("WebSocket disconnected");
        if (animationID) {
            cancelAnimationFrame(animationID);
        }
    };
}

function sendPlayerState() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }

    const playerState = {
        type: "player_update",
        data: {
            position: spaceship.position,
            rotation: spaceship.rotation,
            velocity: spaceship.velocity,
            projectiles: projectiles.map((p) => ({
                id: p.id,
                position: p.position,
                velocity: p.velocity,
                radius: p.radius,
            })),
        },
    };

    ws.send(JSON.stringify(playerState));
}

function endGame() {
    console.log("Game Over!");
    if (animationID) {
        cancelAnimationFrame(animationID);
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "game_over" }));
        ws.close();
    }

    // Display game over screen
    c.fillStyle = "rgba(0, 0, 0, 0.7)";
    c.fillRect(0, 0, canvas.width, canvas.height);
    c.fillStyle = "white";
    c.font = "60px Arial";
    c.textAlign = "center";
    c.fillText("GAME OVER", canvas.width / 2, canvas.height / 2);
    c.font = "30px Arial";
    c.fillText(`Final Score: ${gameState.playerScore}`, canvas.width / 2, canvas.height / 2 + 60);
}

initializeWebSocket();

