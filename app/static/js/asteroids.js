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

//Creating a spaceship
class SpaceShip {
    constructor({ position, velocity }) {
        this.position = position;
        this.velocity = velocity;
        this.rotation = 0;
    }

    draw() {

        // Rotates the ship 
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

    // Update spaceship position every frame
    update() {
        this.draw();
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;

    }

    // Get the vertices of ship at any rotation and store them in an array
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
        ]
    }
}

class Projectiles {
    constructor({ position, velocity }) {
        this.position = position;
        this.velocity = velocity;
        this.radius = 5;
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

const spaceship = new SpaceShip({

    position: { x: canvas.width / 2, y: canvas.height / 2 },
    velocity: { x: 0, y: 0 },

});

const keys = {
    w: {
        pressed: false
    },
    a: {
        pressed: false
    },
    d: {
        pressed: false
    },
};


//Creating asteroids
class Asteroid {
    constructor({ position, velocity, radius }) {
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
            c.arc(0, 0, this.radius, 0, Math.PI * 2, false);
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

    if (distance <= circle1.radius + circle2.radius) {
        return true;
    }

    else {
        return false;
    }

}

// Checks collision between a circle (asteroid) and a triangle (spaceship)
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

        // Calculate distance from circle center to closest point
        dx = closestX - circle.position.x;
        dy = closestY - circle.position.y;

        let distance = Math.sqrt(dx * dx + dy * dy);

        // If distance is less than or equal to radius collision happens
        if (distance <= circle.radius) {
            return true;
        }
    }
}

// Checks if a point (x, y) lies within a given line segment
function isPointOnLineSegment(x, y, begin, end) {

    return (
        x >= Math.min(begin.x, end.x) &&
        x <= Math.max(begin.x, end.x) &&
        y >= Math.min(begin.y, end.y) &&
        y <= Math.max(begin.y, end.y)
    )
}

const Spaceship_Speed = 4;
const Rotate_Speed = 0.05;
const Projectile_Speed = 10;
const Friction = 0.95;

// Animate Asteroids and spaceship
function animate() {
    const animationID = window.requestAnimationFrame(animate);
    c.fillStyle = "black";
    c.fillRect(0, 0, canvas.width, canvas.height);

    spaceship.update();

    c.fillStyle = "white";
    c.font = "24px Arial";
    c.textAlign = "right";
    c.fillText(`Score: ${score}`, canvas.width - 20, 40);

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

        // Remove projectiles that are off screen
        if (
            projectile.position.x + projectile.radius < 0 ||
            projectile.position.x - projectile.radius > canvas.width ||
            projectile.position.y - projectile.radius > canvas.height ||
            projectile.position.y + projectile.radius < 0) {
            projectiles.splice(i, 1);
        }
    }

    if (keys.w.pressed) {

        spaceship.velocity.x = Math.cos(spaceship.rotation) * Spaceship_Speed;
        spaceship.velocity.y = Math.sin(spaceship.rotation) * Spaceship_Speed;
    }
    else if (!keys.w.pressed) {
        spaceship.velocity.x *= Friction;
        spaceship.velocity.y *= Friction;
    }

    if (keys.a.pressed) {
        spaceship.rotation -= Rotate_Speed;
    }

    else if (keys.d.pressed) {
        spaceship.rotation += Rotate_Speed;
    }

    // Update and draw asteroids
    for (let i = asteroids.length - 1; i >= 0; i--) {

        const asteroid = asteroids[i];
        asteroid.update();

        if (circleTriangleCollision(asteroid, spaceship.getVertices())) {
            window.cancelAnimationFrame(animationID);
            clearInterval(intervalID);
        }

        // Remove asteroids that are off screen
        if (
            asteroid.position.x + asteroid.radius < 0 ||
            asteroid.position.x - asteroid.radius > canvas.width ||
            asteroid.position.y + asteroid.radius < 0 ||
            asteroid.position.y - asteroid.radius > canvas.height) {
            asteroids.splice(i, 1);
        }

        // For projectiles colliding with asteroids and splitting them into smaller asteroids
        for (let j = projectiles.length - 1; j >= 0; j--) {
            const projectile = projectiles[j];

            if (circleCollide(projectile, asteroid)) {

                if (asteroid.radius > 30) {
                    const newRadius = asteroid.radius / 2;
                    const randomSplit = Math.random() * Math.PI * 2;

                    asteroids.push(new Asteroid({
                        position: {
                            x: asteroid.position.x,
                            y: asteroid.position.y,
                        },
                        velocity: {
                            x: Math.cos(spaceship.rotation) * 2,
                            y: Math.sin(spaceship.rotation) * 2,
                        },
                        radius: newRadius,
                    }));

                    asteroids.push(new Asteroid({
                        position: {
                            x: asteroid.position.x,
                            y: asteroid.position.y,
                        },
                        velocity: {
                            x: -Math.cos(randomSplit) * 2,
                            y: -Math.sin(randomSplit) * 2,
                        },
                        radius: newRadius,
                    }));

                }
                if (asteroid.radius > 40) {
                    score += 3; // big
                }
                else if (asteroid.radius > 20) {
                    score += 2; // medium
                }
                else {
                    score += 1; // small
                }

                // Remove asteroid and projectile
                asteroids.splice(i, 1);
                projectiles.splice(j, 1);
                break;
            }
        }
    }
}

// Movement keys
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
            projectiles.push(new Projectiles({
                position: {
                    x: spaceship.position.x + Math.cos(spaceship.rotation) * 30,
                    y: spaceship.position.y + Math.sin(spaceship.rotation) * 30,
                },
                velocity: {
                    x: Math.cos(spaceship.rotation) * Projectile_Speed,
                    y: Math.sin(spaceship.rotation) * Projectile_Speed,
                }
            }))
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

const projectiles = [];
const asteroids = [];

let difficulty = 1;
let spawnInterval = 3000;
let intervalID;
let score = 0;

animate();

const difficultyInterval = window.setInterval(() => {
    // Increase difficulty and spawn rate every 15 seconds
    difficulty += 0.5;

    // Decrease spawn interval but not less than 600ms
    spawnInterval = Math.max(600, spawnInterval - 200);

    clearInterval(intervalID);
    startSpawingAsteroids();

}, 15000);

function spawnAsteroid() {

    const index = Math.floor(Math.random() * 4);

    let x, y;
    let vx, vy;
    let radius = 60 * Math.random() + 30;

    switch (index) {

        case 0: // left
            x = 0 - radius;
            y = Math.random() * canvas.height;
            vx = 1;
            vy = 0;
            break;

        case 1: // bottom
            x = Math.random() * canvas.width;
            y = canvas.height + radius;
            vx = 0;
            vy = -1;
            break;

        case 2: // right
            x = canvas.width + radius;
            y = Math.random() * canvas.height;
            vx = -1;
            vy = 0;
            break;

        case 3: // top
            x = Math.random() * canvas.width;
            y = 0 - radius;
            vx = 0;
            vy = 1;
            break;
    }

    // Increase asteroids speed over time
    const Asteroid_Speed = (Math.random() * 1 + 0.5) * difficulty;
    vx *= Asteroid_Speed;
    vy *= Asteroid_Speed;

    asteroids.push(new Asteroid({
        position: {
            x: x,
            y: y,
        },
        velocity: {
            x: vx,
            y: vy,
        },
        radius,
    }));
}
function startSpawingAsteroids() {
    intervalID = window.setInterval(() => {
        const spawnCount = Math.floor(difficulty);
        for (let i = 0; i < spawnCount; i++) {
            spawnAsteroid();
        }
    }, spawnInterval);
}

startSpawingAsteroids();

