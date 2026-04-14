const canvas = document.getElementById("canvas");
const c = canvas.getContext("2d");

const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|Tablet|Windows Phone|Kindle|Silk/i.test(navigator.userAgent);

if (isMobile) {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const joystick = document.getElementById('joystick-container');
    const shootBtn = document.getElementById('mobile-shoot');
    if (joystick) joystick.style.display = 'block';
    if (shootBtn) shootBtn.style.display = 'block';

    setupMobileControls();
   
    window.addEventListener('resize', () => {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
} else {
    canvas.width = 1280;
    canvas.height = 720;
}

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
let opponentShip = null;
let opponentName = null;
let opponentSprite = null;
let ws = null;
let isGameOver = false;

let asteroidsDestroyedCount = 0;
let gameStartTime = Date.now();

//team stats
let teamScore = 0;
let teamAsteroidsDestroyed = 0;
let gameOverMode = null;

class SpaceShip {
    constructor({ position, velocity }) {
        this.position = position;
        this.velocity = velocity;
        this.rotation = 0;
        this.sprite = new Image();
        this.sprite.src = '/static/Asteroids Asset Pack/sprites/spaceship/spaceship_thrust.png';
    }

    setSprite(spriteName) {
        this.sprite.src = `/static/Asteroids Asset Pack/sprites/spaceship/${spriteName}`;
    }

draw() {
    c.save();
    c.translate(this.position.x, this.position.y);
    c.rotate(this.rotation + Math.PI / 2);

    // Maintain aspect ratio
    const maxSize = 40;
    let drawWidth = maxSize;
    let drawHeight = maxSize;
    
    if (this.sprite.complete && this.sprite.naturalWidth > 0) {
        const aspectRatio = this.sprite.naturalWidth / this.sprite.naturalHeight;
        if (aspectRatio > 1) {
            drawHeight = maxSize / aspectRatio;
        } else {
            drawWidth = maxSize * aspectRatio;
        }
    }
    
    c.drawImage(this.sprite, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);

    if (keys.w.pressed) {
        c.beginPath();
        c.moveTo(-5, 10); 
        c.lineTo(0, 25);  
        c.lineTo(5, 10);
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
    constructor({ position, rotation, sprite }) {
        this.position = position;
        this.rotation = rotation;
        this.sprite = new Image();
        if (sprite) {
            this.sprite.src = `/static/Asteroids Asset Pack/sprites/spaceship/${sprite}`;
        } else {
            this.sprite.src = '/static/Asteroids Asset Pack/sprites/spaceship/spaceship_thrust.png';
        }
    }

    draw(color = "#E1B100") {
        c.save();
        c.translate(this.position.x, this.position.y);
        c.rotate(this.rotation + Math.PI / 2);

        // Maintain aspect ratio
        const maxSize = 40;
        let drawWidth = maxSize;
        let drawHeight = maxSize;
        
        if (this.sprite.complete && this.sprite.naturalWidth > 0) {
            const aspectRatio = this.sprite.naturalWidth / this.sprite.naturalHeight;
            if (aspectRatio > 1) {
                drawHeight = maxSize / aspectRatio;
            } else {
                drawWidth = maxSize * aspectRatio;
            }
        }
        
        c.drawImage(this.sprite, -drawWidth / 2, -drawHeight / 2, drawWidth, drawHeight);

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
    space: { pressed: false },
};

const mobileInput = {
    active: false,
    x: 0,
    y: 0
};


const projectiles = [];
let animationID = null;
let lastFireTime = 0;
const FIRE_RATE = 125; // milliseconds between shots

const stars = [];
for (let i = 0; i < 100; i++) {
    stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2,
    });
}

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
            keys.space.pressed = true;
            event.preventDefault();
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
        case "Space":
            keys.space.pressed = false;
            event.preventDefault();
            break;
    }
});

function animate() {
    animationID = window.requestAnimationFrame(animate);

    c.fillStyle = "black";
    c.fillRect(0, 0, canvas.width, canvas.height);

    c.fillStyle = "white";
    for (let star of stars) {
        c.beginPath();
        c.arc(star.x, star.y, star.size, 0, Math.PI * 2);
        c.fill();
    }

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


    let totalProjectilesCount = 0;
    for (const [playerIdInState, playerData] of Object.entries(gameState.players)) {
        if (playerData.projectiles && playerData.projectiles.length > 0) {
            totalProjectilesCount += playerData.projectiles.length;
            playerData.projectiles.forEach((proj) => {
                const size = 4;
                c.save();
                c.translate(proj.position.x, proj.position.y);
                
                if (playerIdInState === playerId) {
                    c.fillStyle = "white";
                    c.strokeStyle = "rgba(255, 255, 255, 0.8)";
                } else {
                    c.fillStyle = "#FFD700";
                    c.strokeStyle = "rgba(255, 215, 0, 0.8)";
                }
                
                c.fillRect(-size/2, -size/2, size, size);
                c.lineWidth = 1;
                c.strokeRect(-size/2, -size/2, size, size);
                c.restore();
            });
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
        if (!opponentShip || opponentShip.sprite.src.split('/').pop() !== opponentSprite) {
            opponentShip = new OpponentShip(opponentData);
        } else {
            opponentShip.position = opponentData.position;
            opponentShip.rotation = opponentData.rotation;
        }
        opponentShip.draw("#E1B100");
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

    if (mobileInput.active) {
        const force = Math.min(1, Math.sqrt(mobileInput.x ** 2 + mobileInput.y ** 2));

        spaceship.velocity.x = mobileInput.x * Spaceship_Speed * 0.6;
        spaceship.velocity.y = mobileInput.y * Spaceship_Speed * 0.6;

        if (force > 0.1) {
            spaceship.rotation = Math.atan2(mobileInput.y, mobileInput.x);
        }
    }

    if (keys.space.pressed) {
        sendShootEvent();
    }

    renderStats();
    sendPlayerState();
}

let difficulty = 1;
let spawnInterval = 3000;

const difficultyInterval = window.setInterval(() => {
    difficulty += 0.4;
    spawnInterval = Math.max(800, spawnInterval - 130);

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
                rotation: opponentPlayerData.rotation,
                sprite: opponentSprite
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

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
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

            teamScore = 0;
            teamAsteroidsDestroyed = 0;
            
            if (message.ship_sprite) {
                spaceship.setSprite(message.ship_sprite);
            }
            if (message.mode === "multiplayer") {
                gameMode = "multiplayer";
            }
        }

        if (message.type === "player_joined") {
            if (message.player_id !== playerId) {
                opponentName = message.username;
                if (message.ship_sprite) {
                    opponentSprite = message.ship_sprite;
                }
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
                    score: playerData.score,
                    projectiles: playerData.projectiles || []
                };
            }

            const selfData = gameState.players[playerId];
            if (selfData) {
                gameState.playerLives = selfData.lives;
                gameState.playerScore = selfData.score;
            }

            if (gameMode === "multiplayer") {
                teamScore = 0;
                for (const player of Object.values(gameState.players)) {
                    teamScore += player.score || 0;
                }
            }

            if (data.collisions && data.collisions.length > 0) {
                data.collisions.forEach((collision) => {
                    if (collision.type === "asteroid_destroyed") {
                        asteroidsDestroyedCount++;

                        if (gameMode === "multiplayer") {
                            teamAsteroidsDestroyed++;
                        }
                    } else if (collision.type === "ship_hit") {
                    }
                });
            }

            if (gameMode === "multiplayer") {
                const allPlayers = Object.values(gameState.players || {});
                const anyPlayerDead = allPlayers.some(p => p.lives <= 0);
                if (anyPlayerDead) {
                    endGame();
                }
            } else {
                if (selfData && selfData.lives <= 0) {
                    endGame();
                }
            }
        }
    };

    ws.onerror = (error) => {
    };

    ws.onclose = () => {
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
        },
    };

    ws.send(JSON.stringify(playerState));
}

function sendShootEvent() {
    const now = Date.now();
    if (now - lastFireTime < FIRE_RATE) {
        return; // Fire rate cooldown not met
    }
    lastFireTime = now;

    if (!ws || ws.readyState !== WebSocket.OPEN) {
        return;
    }

    const shootEvent = {
        type: "shoot",
        data: {
            position: {
                x: spaceship.position.x + Math.cos(spaceship.rotation) * 30,
                y: spaceship.position.y + Math.sin(spaceship.rotation) * 30,
            },
            velocity: {
                x: Math.cos(spaceship.rotation) * Projectile_Speed,
                y: Math.sin(spaceship.rotation) * Projectile_Speed,
            },
        },
    };

    ws.send(JSON.stringify(shootEvent));
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function endGame() {
    const timeSurvived = Math.floor((Date.now() - gameStartTime) / 1000);
    
    if (animationID) cancelAnimationFrame(animationID);
    if (ws && ws.readyState === WebSocket.OPEN) ws.close();
    
    gameOverMode = gameMode;
    
    if (gameMode === "solo") {
        // Solo game over
        document.getElementById("canvas").style.display = "none";
        document.getElementById("game-over-screen").style.display = "flex";
        document.getElementById("final-score").textContent = gameState.playerScore;
        document.getElementById("asteroids-destroyed").textContent = asteroidsDestroyedCount;
        document.getElementById("time-survived").textContent = formatTime(timeSurvived);
    } else {
        // Multiplayer game over
        document.getElementById("canvas").style.display = "none";
        document.getElementById("multiplayer-game-over-screen").style.display = "flex";
        document.getElementById("team-final-score").textContent = teamScore;
        document.getElementById("team-asteroids-destroyed").textContent = teamAsteroidsDestroyed;
        document.getElementById("team-time-survived").textContent = formatTime(timeSurvived);
    }
}

function playAgain() {
    window.location.href = "/app/play/coop";
}

function exitToHome() {
    window.location.href = "/app";
}

function setupMobileControls() {
    if (typeof nipplejs === 'undefined') {
        return;
    }
    
    const container = document.getElementById('joystick-container');
    const shootBtn = document.getElementById('mobile-shoot');
    
    if (!container || !shootBtn) return;
    
    const joystick = nipplejs.create({
        zone: container,
        mode: 'static',
        position: { left: '50%', top: '50%' },
        color: 'white',
        size: 80,
        lockY: false,
        lockX: false
    });
    
    joystick.on('move', (evt, data) => {
        mobileInput.active = true;

        mobileInput.x = data.vector.x;
        mobileInput.y = -data.vector.y;
    });

    joystick.on('end', () => {
        mobileInput.active = false;
        mobileInput.x = 0;
        mobileInput.y = 0;
    });
    
    const preventTouch = (e) => e.preventDefault();
    
    shootBtn.addEventListener('touchstart', (e) => {
        preventTouch(e);
        keys.space.pressed = true;
    });
    
    shootBtn.addEventListener('touchend', (e) => {
        preventTouch(e);
        keys.space.pressed = false;
    });
    
    shootBtn.addEventListener('touchcancel', (e) => {
        preventTouch(e);
        keys.space.pressed = false;
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupMobileControls);
} else {
    setupMobileControls();
}

initializeWebSocket();