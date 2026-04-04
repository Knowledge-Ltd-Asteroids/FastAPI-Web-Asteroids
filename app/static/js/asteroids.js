const canvas = document.getElementById("canvas");
const c = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight; 

c.fillStyle = "black";
c.fillRect(0, 0, canvas.width, canvas.height);

class Asteroid {
    constructor({position, velocity, radius}) {
        this.position = position;
        this.velocity = velocity;   
        this.radius = radius;
    }

    draw(){
        c.beginPath();
        c.arc(this.position.x, this.position.y, this.radius, 0, Math.PI * 2,false);
        c.closePath();
        c.strokeStyle = "white";
        c.stroke();
    }

    update(){
        this.draw();
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;
    }
}

const projectiles = [];
const asteroids = [];

window.setInterval(() => {

    const index = Math.floor(Math.random() * 4);

    let x,y;
    let vx, vy;
    let radius = 50 * Math.random() + 10;

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
    asteroids.push(new Asteroid({position: {
        x: x,
        y: y,
    },
    velocity: {

        x: vx,
        y: vy,

    },
    radius,
     })
    );

}, 3000);

function animate() {
    window.requestAnimationFrame(animate);
    c.fillStyle = "black";
    c.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = asteroids.length - 1; i >= 0; i--) {

        const asteroid = asteroids[i];
        asteroid.update();

    // Remove asteroids that are off screen
        if (
            asteroid.position.x + asteroid.radius < 0 ||
            asteroid.position.x - asteroid.radius > canvas.width ||
            asteroid.position.y + asteroid.radius < 0 ||
            asteroid.position.y - asteroid.radius > canvas.height) {
                asteroids.splice(i, 1);
            }
    }
}

animate();