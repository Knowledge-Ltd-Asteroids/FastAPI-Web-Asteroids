(function() {
    const canvas = document.getElementById('bg-canvas');
    const c = canvas.getContext('2d');
    
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
    
    
    let spritesLoaded = false;
    let loadedCount = 0;
    const totalSprites = 5; 
    
    function spriteLoaded() {
        loadedCount++;
        if (loadedCount >= totalSprites) {
            spritesLoaded = true;
        }
    }
    
    asteroidSprites.big2.onload = spriteLoaded;
    asteroidSprites.medium1.onload = spriteLoaded;
    asteroidSprites.medium2.onload = spriteLoaded;
    asteroidSprites.small1.onload = spriteLoaded;
    asteroidSprites.small2.onload = spriteLoaded;
    
    asteroidSprites.big2.onerror = () => { spritesLoaded = true; };
    
    function resizeCanvas() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    resizeCanvas();
    
    c.fillStyle = 'black';
    c.fillRect(0, 0, canvas.width, canvas.height);
    
    let mouseX = canvas.width / 2;
    let mouseY = canvas.height / 2;
    let mousePresent = false;
    
    const asteroids = [];
    
    let loginBox = {
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        active: false
    };
    
    let boxGlow = 0;
    
    function updateLoginBoxBounds() {
        const card = document.querySelector('.card');
        if (card) {
            const rect = card.getBoundingClientRect();
            loginBox = {
                x: rect.left,
                y: rect.top,
                width: rect.width,
                height: rect.height,
                active: true
            };
        } else {
            loginBox.active = false;
        }
    }
    
    const spriteTypes = [
        { name: 'big2', size: 60, spriteKey: 'big2' },
        { name: 'medium1', size: 40, spriteKey: 'medium1' },
        { name: 'medium2', size: 40, spriteKey: 'medium2' },
        { name: 'small1', size: 25, spriteKey: 'small1' },
        { name: 'small2', size: 25, spriteKey: 'small2' }
    ];
    
    class Asteroid {
        constructor({position, velocity, spriteType}) {
            this.position = position;
            this.velocity = velocity;
            this.spriteType = spriteType;
            this.radius = spriteType.size / 2;
            this.rotation = Math.random() * Math.PI * 2;
            this.rotationSpeed = (Math.random() - 0.5) * 0.02;
            this.highlight = 0;
        }
    
        draw(){
            c.save();
            c.translate(this.position.x, this.position.y);
            this.rotation += this.rotationSpeed;
            c.rotate(this.rotation);
            
            const sprite = asteroidSprites[this.spriteType.spriteKey];
            const size = this.spriteType.size;
            
            if (spritesLoaded && sprite && sprite.complete) {
                c.drawImage(sprite, -size/2, -size/2, size, size);
                
                if (this.highlight > 0) {
                    c.globalAlpha = 0.4;
                    c.drawImage(sprite, -size/2, -size/2, size, size);
                    c.globalAlpha = 1.0;
                    this.highlight--;
                }
            } else {
                c.beginPath();
                c.arc(0, 0, this.radius, 0, Math.PI * 2);
                c.strokeStyle = this.highlight > 0 ? '#E1B100' : 'white';
                c.lineWidth = this.highlight > 0 ? 2.5 : 1.5;
                c.stroke();
                if (this.highlight > 0) this.highlight--;
            }
            
            c.restore();
        }
    
        update(){
            this.draw();
            this.position.x += this.velocity.x;
            this.position.y += this.velocity.y;
            
            if (loginBox.active) {
                const asteroidLeft = this.position.x - this.radius;
                const asteroidRight = this.position.x + this.radius;
                const asteroidTop = this.position.y - this.radius;
                const asteroidBottom = this.position.y + this.radius;
                
                const boxLeft = loginBox.x;
                const boxRight = loginBox.x + loginBox.width;
                const boxTop = loginBox.y;
                const boxBottom = loginBox.y + loginBox.height;
                
                if (asteroidRight > boxLeft && asteroidLeft < boxRight &&
                    asteroidBottom > boxTop && asteroidTop < boxBottom) {
                    
                    const overlapLeft = asteroidRight - boxLeft;
                    const overlapRight = boxRight - asteroidLeft;
                    const overlapTop = asteroidBottom - boxTop;
                    const overlapBottom = boxBottom - asteroidTop;
                    
                    const minOverlap = Math.min(overlapLeft, overlapRight, overlapTop, overlapBottom);
                    
                    if (minOverlap === overlapLeft) {
                        this.position.x = boxLeft - this.radius;
                        this.velocity.x = -this.velocity.x * 0.6;
                    } else if (minOverlap === overlapRight) {
                        this.position.x = boxRight + this.radius;
                        this.velocity.x = -this.velocity.x * 0.6;
                    } else if (minOverlap === overlapTop) {
                        this.position.y = boxTop - this.radius;
                        this.velocity.y = -this.velocity.y * 0.6;
                    } else {
                        this.position.y = boxBottom + this.radius;
                        this.velocity.y = -this.velocity.y * 0.6;
                    }
                    
                    boxGlow = 1.0;
                    
                    const card = document.querySelector('.card');
                    if (card) {
                        card.classList.add('shield-hit');
                        setTimeout(() => card.classList.remove('shield-hit'), 100);
                    }
                }
            }
            
            if (mousePresent) {
                const dx = this.position.x - mouseX;
                const dy = this.position.y - mouseY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance < this.radius) {
                    const angle = Math.atan2(dy, dx);
                    const pushForce = 1.5;
                    
                    this.velocity.x += Math.cos(angle) * pushForce;
                    this.velocity.y += Math.sin(angle) * pushForce;
                    
                    this.position.x = mouseX + Math.cos(angle) * (this.radius + 2);
                    this.position.y = mouseY + Math.sin(angle) * (this.radius + 2);
                                        
                    const maxSpeed = 5;
                    const speed = Math.sqrt(this.velocity.x ** 2 + this.velocity.y ** 2);
                    if (speed > maxSpeed) {
                        this.velocity.x *= maxSpeed / speed;
                        this.velocity.y *= maxSpeed / speed;
                    }
                }
            }
        }
    }
    
    const stars = [];
    for (let i = 0; i < 100; i++) {
        stars.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            size: Math.random() * 2,
        });
    }
    
    function animate() {
        window.requestAnimationFrame(animate);
        
        c.fillStyle = 'black';
        c.fillRect(0, 0, canvas.width, canvas.height);
        
        c.fillStyle = 'white';
        for (let star of stars) {
            c.beginPath();
            c.arc(star.x, star.y, star.size, 0, Math.PI * 2);
            c.fill();
        }
        
        updateLoginBoxBounds();
        
        for (let i = asteroids.length - 1; i >= 0; i--) {
            const asteroid = asteroids[i];
            asteroid.update();
            
            if (
                asteroid.position.x + asteroid.radius < -50 ||
                asteroid.position.x - asteroid.radius > canvas.width + 50 ||
                asteroid.position.y + asteroid.radius < -50 ||
                asteroid.position.y - asteroid.radius > canvas.height + 50
            ) {
                asteroids.splice(i, 1);
            }
        }
        
        if (boxGlow > 0 && loginBox.active) {
            c.strokeStyle = `rgba(225, 177, 0, ${boxGlow * 0.4})`;
            c.lineWidth = 4;
            c.strokeRect(loginBox.x - 4, loginBox.y - 4, loginBox.width + 8, loginBox.height + 8);
            
            c.strokeStyle = `rgba(225, 177, 0, ${boxGlow * 0.2})`;
            c.lineWidth = 2;
            c.strokeRect(loginBox.x - 2, loginBox.y - 2, loginBox.width + 4, loginBox.height + 4);
            
            boxGlow *= 0.9;
        }
    }
    
    function spawnAsteroid() {
        const index = Math.floor(Math.random() * 4);
        let x, y;
        let vx, vy;
        
        const spriteType = spriteTypes[Math.floor(Math.random() * spriteTypes.length)];
        const radius = spriteType.size / 2;
        
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
        
        const AsteroidSpeed = Math.random() * 1.5 + 0.5;
        vx *= AsteroidSpeed;
        vy *= AsteroidSpeed;
        
        asteroids.push(new Asteroid({
            position: { x: x, y: y },
            velocity: { x: vx, y: vy },
            spriteType: spriteType
        }));
    }
    
    window.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
        mousePresent = true;
        
        clearTimeout(window.mouseTimeout);
        window.mouseTimeout = setTimeout(() => {
            mousePresent = false;
        }, 1000);
    });
    
    window.addEventListener('resize', () => {
        resizeCanvas();
        stars.forEach(star => {
            star.x = Math.random() * canvas.width;
            star.y = Math.random() * canvas.height;
        });
        updateLoginBoxBounds();
    });
    
    
    animate();
    window.setInterval(spawnAsteroid, 3000);
    window.setInterval(updateLoginBoxBounds, 100);
})();