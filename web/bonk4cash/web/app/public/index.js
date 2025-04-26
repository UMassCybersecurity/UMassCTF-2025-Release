let ws;

const chatinput = document.getElementById('chatinput');
function sendMessage(){
  if(ws){
    ws.send(chatinput.value)
    chatinput.value = '';
  }
}

let queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const result = urlParams.get('result');
if(result){
  alert(decodeURI(result));
}

const chatbutton = document.getElementById('chatbutton')
chatbutton.addEventListener('click', sendMessage)

const chatbox = document.getElementById('chat')
async function initChat(){
  const key = await (await fetch("/chatkey", {method:"post", credentials:'include'})).text();

  ws = new WebSocket("/chat")
  ws.onopen = (event) => {
    ws.send(key)
  }
  ws.onmessage = (event) => {
    console.log(`received ${event.data}`)
    if(event.data !== "successfully authorized"){
      chatbox.innerHTML = `${event.data}<br>\n` + chatbox.innerHTML
    }
  }
  const resp = await fetch("/transcript");
  if(resp.ok){
    chatbox.innerHTML = await resp.text();
  }else{
    chatbox.innerHTML = "<br />Failed to load messages"
  }
}
chatinput.addEventListener('keypress', (e) => {
   if(e.key === "Enter"){
    sendMessage();
   }
});

initChat();

// game logic =========================
const canvas = document.getElementById("game");
const ctx = canvas.getContext("2d");
// Set canvas size
canvas.width = window.innerHeight;
canvas.height = window.innerHeight * 0.5;

// Ball class
class Ball {
  constructor(x, y, radius, color, dx, dy) {
    this.x = x;
    this.y = y;
    this.radius = radius;
    this.color = color;
    this.dx = dx; // horizontal velocity
    this.dy = dy; // vertical velocity
    this.ddx = 0;
    this.gravity = 0.1;
    this.specialGravity = 0;
    this.friction = 0.1;
    this.weight = 1;
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
    if(this.jumping && this.jumpTime < 4){
      this.jumpTime += 0.1;
      this.dy = -0.5*(16-this.jumpTime*this.jumpTime);
    }
    else if (this.y + this.radius + this.dy > canvas.height) {
      this.jumpTime = 0;
      this.dy = 0;
    } else {
      this.jumpTime = 6;
      this.dy += this.gravity+this.specialGravity - 0.1*(this.dy-6);
    }
    this.dx += this.ddx/this.weight;
    this.dx *= 0.99;
    this.x += this.dx;
    this.y += this.dy;

    this.draw();

    // lose if outside wall
    if (this.x - this.radius + this.dx > canvas.width || this.x + this.radius <= 0) {
      return false;
    }
    return true;
  }
}

let player;
let opponent;

const reset = () => {
  player = new Ball(canvas.width*0.25, canvas.height/2, 25, '#0000FF', 0, 0)
  opponent = new Ball(canvas.width*0.75, canvas.height/2, 25, '#FF0000', 0, 0)
};
reset();

const project = (n1x, n1y, v2x, v2y) => {
  const scale = (n1x*v2x+n1y*v2y)
  return {x: n1x*scale, y: n1y*scale}
}

const checkCollision = () => {
  const normalMag = Math.sqrt(Math.pow(player.x-opponent.x, 2)+Math.pow(player.y-opponent.y,2));
  if(normalMag<50){
    const normal = {x: (player.x-opponent.x)/normalMag, y:(player.y-opponent.y)/normalMag};
    const playerNorm = project(normal.x, normal.y, player.dx, player.dy);
    const opponentNorm = project(normal.x, normal.y, opponent.dx, opponent.dy);

    const oppvsplayer = opponent.weight/player.weight
    const playervsopp = player.weight/opponent.weight
    player.dx = player.dx + oppvsplayer * opponentNorm.x - 1 * playerNorm.x;
    player.dy = player.dy + oppvsplayer * opponentNorm.y - 1 * playerNorm.y;
    opponent.dx = opponent.dx + playervsopp * playerNorm.x - 1 * opponentNorm.x;
    opponent.dy = opponent.dy + playervsopp * playerNorm.y - 1 * opponentNorm.y;
  }
  let newNormalMag = Math.sqrt(Math.pow(player.x-opponent.x, 2)+Math.pow(player.y-opponent.y,2));
  while(newNormalMag < 50){
    const normal = {x: (player.x-opponent.x)/normalMag, y:(player.y-opponent.y)/normalMag};
    player.x += normal.x;
    player.y += normal.y
    newNormalMag = Math.sqrt(Math.pow(player.x-opponent.x, 2)+Math.pow(player.y-opponent.y,2));
  }
}


const moveOpponent = () => {
  if(player.x < opponent.x-100){
    opponent.ddx = -0.2;
  }else if(player.x > opponent.x +100){
    opponent.ddx = 0.2;
  }else{
    opponent.ddx = 0;
  }
  if(player.y < opponent.y-20){
    opponent.jumping = true;
  }else{
    opponent.jumping = false;
  }
  const normalMag = Math.sqrt(Math.pow(player.x-opponent.x, 2)+Math.pow(player.y-opponent.y,2));
  if(normalMag < 100){
    opponent.weight = 3;
    opponent.color = '#FFAAAA'
  }else{
    opponent.weight = 1;
    opponent.color = '#FF0000'
  }
}

const delay = ms => new Promise(res => setTimeout(res, ms));

// Animation loop
function animate() {
  requestAnimationFrame(animate);
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  moveOpponent();
  checkCollision();
  let playerAlive = player.update();
  let opponentAlive = opponent.update();
  if(!playerAlive){
    reset();
    alert("you lost!")
  }else if (!opponentAlive){
    reset();
    alert("you won $100!")
    fetch("/win", {method: 'post'});
  }
}

animate();


// Resize canvas on window resize
window.addEventListener("resize", () => {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
});

document.addEventListener('keydown', (e) => {
  switch(e.key){
    case "ArrowLeft":
      player.ddx = -0.2;
      break;
    case "ArrowRight":
      player.ddx = 0.2;
      break;
    case "ArrowUp":
      player.jumping = true;
      break;
    case "ArrowDown":
      player.specialGravity = 0.2
      break;
    case " ":
      player.weight = 3;
      player.color = '#AAAAFF'
      break;
  }
});

document.addEventListener('keyup', (e) => {
  switch(e.key){
    case "ArrowLeft":
      if(player.ddx < 0) player.ddx = 0;
      break;
    case "ArrowRight":
      if(player.ddx > 0) player.ddx = 0;
      break;
    case "ArrowUp":
      player.jumping = false;
      break;
    case "ArrowDown":
      player.specialGravity = 0;
      break;
    case " ":
      player.weight = 1;
      player.color = '#0000FF'
      break;
  }
})