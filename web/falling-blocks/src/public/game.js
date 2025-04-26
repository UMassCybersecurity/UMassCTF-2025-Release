const ws = new WebSocket(`ws://${window.location.hostname}`)
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

canvas.width = canvas.offsetWidth;
canvas.height = canvas.offsetHeight;

let player = { x: canvas.width / 2 - 20, y: canvas.height - 60, width: 40, height: 40 };
let obstacles = [];
let score = 0;
let speed = 2;

document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft' && player.x > 0) player.x -= 20;
    if (e.key === 'ArrowRight' && player.x < canvas.width - player.width) player.x += 20;
    ws.send(JSON.stringify({ playerX: player.x }));
});

function updateGame() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = 'blue';
    ctx.fillRect(player.x, player.y, player.width, player.height);

    if (Math.random() < 0.02) {
        obstacles.push({ x: Math.random() * (canvas.width - 40), y: 0, width: 40, height: 40 });
    }

    ctx.fillStyle = 'red';
    for (let i = 0; i < obstacles.length; i++) {
        obstacles[i].y += speed;
        ctx.fillRect(obstacles[i].x, obstacles[i].y, obstacles[i].width, obstacles[i].height);
        
        if (
            player.x < obstacles[i].x + obstacles[i].width &&
            player.x + player.width > obstacles[i].x &&
            player.y < obstacles[i].y + obstacles[i].height &&
            player.y + player.height > obstacles[i].y
        ) {
            ws.send(JSON.stringify({ type: 'gameOver', time: new Date().toLocaleTimeString(), score: score }));
            alert('Game Over! Score: ' + score);
            document.location.reload();
        }
    }
    score++;
    if (score % 100 === 0) speed += 0.5;
    requestAnimationFrame(updateGame);
}

window.addEventListener('resize', () => {
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;
    player.x = canvas.width / 2 - 20;
    player.y = canvas.height - 60;
});

updateGame();