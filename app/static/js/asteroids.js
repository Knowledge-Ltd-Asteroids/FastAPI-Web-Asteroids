const canvas = document.getElementById("canvas");
const c = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight; 

c.fillStyle = "black";
c.fillRect(0, 0, canvas.width, canvas.height);

//Creating a spaceship
class SpaceShip {
    constructor({position, velocity}){
        this.position = position;
        this.velocity = velocity;
        this.rotation = 0;
    }

    draw(){

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
        c.restore();
        }

    // Update spaceship position every frame
    update(){
        this.draw();
        this.position.x += this.velocity.x;
        this.position.y += this.velocity.y;

        }

    }

const spaceship = new SpaceShip({

    position:{x: canvas.width / 2, y: canvas.height / 2}, 
    velocity:{x: 0, y: 0},

    });

    const keys ={
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

const Speed = 3;
const Rotate_Speed = 0.03;

// Animate Asteroids and spaceship
function animate() {
    window.requestAnimationFrame(animate);
    c.fillStyle = "black";
    c.fillRect(0, 0, canvas.width, canvas.height);

        spaceship.update();

        if (keys.w.pressed) {
            
            spaceship.velocity.x = Math.cos(spaceship.rotation) * Speed;
            spaceship.velocity.y = Math.sin(spaceship.rotation) * Speed;
        } 
        else{
            spaceship.velocity.x = 0;
            spaceship.velocity.y = 0;
        }

        if(keys.a.pressed){
            spaceship.rotation -= Rotate_Speed;
        }

        else if(keys.d.pressed){
            spaceship.rotation += Rotate_Speed;
        }

    // Update and draw asteroids
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

    // Movement keys
    window.addEventListener("keydown", (event) => {
        switch(event.code){
            case "KeyW":
                keys.w.pressed = true;
                break;
            case "KeyA":
                keys.a.pressed = true;
                break;  
            case "KeyD":
                keys.d.pressed = true;
                break;
        }
    });

        window.addEventListener("keyup", (event) => {
        switch(event.code){
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


animate();

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
     })
    );

}, 3000);

