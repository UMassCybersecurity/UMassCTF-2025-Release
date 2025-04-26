
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

// Set canvas size
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

// Ball class
class Ball {
  constructor(x, y, radius, color, dx, dy) {
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.color = color;
    this.dx = dx; // horizontal velocity
    this.dy = dy; // vertical velocity
    this.gravity = 0.5;
    this.friction = 0.8;
  }

  draw() {
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2, false);
    ctx.fillStyle = this.color;
    ctx.fill();
    ctx.closePath();
  }

  update() {
    // Gravity effect
    if (this.y + this.radius + this.dy > canvas.height) {
      if(this.dy < 1){
        return false;
      }
      this.dy = -this.dy * this.friction;
    } else {
      this.dy += this.gravity;
    }


    this.x += this.dx;
    this.y += this.dy;

    this.draw();

    // delete if outside wall
    if (this.x - this.radius + this.dx > canvas.width || this.x + this.radius <= 0) {
      return false;
    }
    return true;
  }
}

// Create multiple balls
let balls = [];
function getRandomColor() {
  var letters = '0123456789ABCDEF';
  var color = '#';
  for (var i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  balls = balls.filter(ball => ball.update())
}

animate();

const delay = ms => new Promise(res => setTimeout(res, ms));
let addBalls = async () => {
  if(!document.cookie.includes("no_balls")){
  for (let i = 0; i < 5; i++) {
    const radius = Math.random() * 20 + 10;
    const x = Math.random() * (canvas.width - radius * 2) + radius;
    const y = Math.random() * (canvas.height - radius * 2) - canvas.height;
    const dx = (Math.random() - 0.5) * 8;
    const dy = (Math.random() - 0.5) * 8;
    const color = getRandomColor();
    balls.push(new Ball(x, y, radius, color, dx, dy));
  }
  }else{
    balls = [];
  }
  await delay(2000);
  addBalls();
}

addBalls();

// Resize canvas on window resize
window.addEventListener("resize", () => {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
});