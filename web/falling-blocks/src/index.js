const WebSocket = require('ws');
const express = require('express');
const http = require('http');
const path = require('path');
const redis = require('redis');
const bodyParser = require('body-parser');
const cookieParser = require('cookie-parser');
const utils = require('./utils.js');
const scoreboard = require('./scoreboard.js');
const jwt = require('jsonwebtoken');
const crypto = require('crypto');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });
app.use(cookieParser());
app.use(bodyParser.urlencoded({ extended: true }));

app.use(express.static(path.join(__dirname, 'public')));

const client = redis.createClient({url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`});
const port = 80;

(async () => {
    client.on('error', err => console.log('Redis Client Error', err));
    await client.connect();
    const dream = { "username": "Dream", "password": crypto.randomBytes(64).toString('hex'), "score": 10001, 'tokens': '0' };
    await client.HSET("Dream", dream);
    await utils.createToken("Dream", client);
    const ssundae = { "username": "Ssundae", "password": crypto.randomBytes(64).toString('hex'), "score": 66666, 'tokens': '0' };
    await client.HSET("Ssundae", ssundae);
    await utils.createToken("Ssundae", client);
    const muselk = { "username": "Muselk", "password": crypto.randomBytes(64).toString('hex'), "score": 30303, 'tokens': '0' };
    await client.HSET("Muselk", muselk);
    await utils.createToken("Muselk", client);
    scoreboard.addScore(dream.score, dream.username);
    scoreboard.addScore(ssundae.score, ssundae.username);
    scoreboard.addScore(muselk.score, muselk.username);
})();

wss.on('connection', (ws, req) => {
    console.log('Player connected');
    
    ws.on('message', async (message) => {
        try {
            const token = cookieParser.JSONCookies(
                require('cookie').parse(req.headers.cookie || '')
            );
            const user = jwt.verify(token.user, process.env.SECRET_TOKEN);
            let userdata = { "username": user.username };
            const data = JSON.parse(message);

            if (data.type && data.time && data.score) {
                if (data.type === 'gameOver') {
                    let score = data.score;
    
                    if (score > 10000) {
                        data.score = 0;
                    }
    
                    userdata = Object.assign(userdata, data);
                    userdata.score = Math.max(userdata.score, await client.HGET(userdata.username, "score"));
                    await client.HSET(userdata.username, userdata);
                    await scoreboard.addScore(userdata.score, userdata.username);
                }
            }
        } catch (err) {
            console.error('Error:', err);
        }
    });

    ws.on('close', () => {
        console.log('Player disconnected');
    });
});

app.get('/game', utils.authMiddleware, async (req, res) => {
    res.sendFile(path.join(__dirname, "public", "game.html"));
})


app.get("/", (req, res) => res.sendFile(path.join(__dirname, "public", "index.html")));
app.get("/login", (req, res) => res.sendFile(path.join(__dirname, "public", "login.html")));
app.get("/scoreboard", (req, res) => res.sendFile(path.join(__dirname, "public", "board.html")))

app.get('/api/scores', async (req, res) => {
    res.json(await scoreboard.getScore());
});

app.get('/logout', utils.authMiddleware, async (req, res) => {
    try {
        if (req.user.username !== await client.HGET(req.user.username, 'username')) {
            return res.json({ "message": "Stop cheating!" });
        }
        const score = await client.HGET(req.user.username, 'score');
        if (score > 10000) {
            return res.json({ "message": process.env.FLAG });
        }
        res.clearCookie("user");
        res.redirect("/login");
    } catch (err) {
        console.error('Error:', err);
    }
});

app.post('/register', async (req, res) => {
    try {
        const newuser = req.body;
        const username = newuser.username;
        const password = newuser.password;
        if (username && typeof username == 'string' && username.match(/([a-z|A-Z|0-9])+/g) && password && typeof password == 'string') {
        const isUserTaken = await client.exists(username);
        if (isUserTaken) {
            return res.json({ "error": "Username is taken." });
        }
        else {
            const userdata = { 'username': username, 'password': password, 'score': 0, 'tokens': '0' };
            await client.HSET(username, userdata);
            await utils.createToken(username, client);

            console.log(await client.HGETALL(username));
            return res.redirect('/login');
        }
        }
        return res.json({ "error": "Username or password is invalid." });
    } catch (err) {
        console.error('Error:', err);
    }
})

app.post('/login', async (req, res) => {
    try {
        const user = req.body;
        const username = user.username;
        const password = user.password;
        if (username && password && typeof username == 'string' && typeof password == 'string') {
            if (!(await client.exists(username))) {
                return res.json({ "error": "Go register an account first." });
            }
            if (username !== await client.HGET(username, 'username')) {
                return res.json({ "message": "Stop cheating!" });
            }
            if (password === await client.HGET(username, 'password')) {
                res.cookie("user", await client.HGET(username, 'tokens'), {
                    httpOnly: true
                });
                return res.redirect('/game');
            }
            else {
                return res.json({ "message": "Invalid Credentials." });
            }
        }
        else {
            return res.json({ "error": "Username or password is invalid." });
        }
    } catch (e) {
        console.error('Error:', err);
    }
})

server.listen(port, () => {
    console.log(`Falling Blocks on port ${port}`);
});
