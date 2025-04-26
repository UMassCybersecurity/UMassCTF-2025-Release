const express = require('express');
const websocket_express = require('websocket-express');
const app = new websocket_express.WebSocketExpress();
const cookieParser = require('cookie-parser');

const redis = require('redis');
const client = redis.createClient({
  'url': `redis://${process.env.REDIS}:6379`
});
client.on('error', err => console.log('Redis Client Error', err));
client.connect();

const createDOMPurify = require('dompurify');
const { JSDOM } = require('jsdom');

const window = new JSDOM('').window;
const DOMPurify = createDOMPurify(window);


const bot = require('./bot.js');
const utils = require('./util.js');

const port = process.env.SERVER_PORT;
const nginxport = process.env.NGINX_PORT;
const nginxhost = process.env.NGINX_HOST;
let chatMessages = [];
const keys = {};
const sockets = [];
const npcs = ["EpicElectricBoogaloo","Tyler ninja blevins","xXx_n00bS1ay3r_xXx", "TylerGonzalez2012", "Alice from accounting"];
const npcMessages = [
  "glhf",
  "gg ez",
  "chat is this cooked",
  "gg no re",
  "chat is this real",
  "ballsisters, is it over?",
  "I'm in my bonk arc, I'm such a bonkpilled cashmaxxer",
  "look at me I'm dababy",
  "lets goooo",
  "skill issue",
];
const getRandom = (arr) => {
  return arr[Math.floor(Math.random() * arr.length)];
}
const addRandomMessage = () => {
  const msg = getRandom(npcMessages)
  const name = getRandom(npcs);
  const message = `[${name}] ${msg}`
  chatMessages.unshift(message);
  sockets.forEach((w) => {
    w.send(DOMPurify.sanitize(message));
  })
}
const delay = ms => new Promise(res => setTimeout(res, ms));
const messageDelay = async () => {
  await delay(5000);
  addRandomMessage();
  await delay(2000);
  addRandomMessage();
}

app.use(cookieParser());
app.use(express.json());
app.use(express.urlencoded({ extended: false }));
app.set('view engine', 'ejs');
app.use('/static', express.static('public'))

app.get('/', utils.indexMiddleware, async (req, res) => {
    messageDelay();
    res.render("index.ejs", {opponent: getRandom(npcs), self: req.user.username})
});

app.post("/chatkey", utils.authMiddleware, async (req, res) => {
  const key = crypto.getRandomValues(new BigUint64Array(1))[0].toString(36);
  keys[key] = req.user.username
  return res.send(key);
})

app.ws("/chat", async (req, res) => { 
  const ws = await res.accept();
  const user = await utils.authMiddlewareWS(ws, keys);
  if(!user){
    return;
  }
  console.log(`authorized ${user}`)
  const name = user;
  ws.send("successfully authorized");

  sockets.push(ws);

  ws.on('message', (msg) => {
    messageDelay();
    chatMessages.unshift(`[${name}] ${msg}`);
    sockets.forEach((w) => {
      w.send(DOMPurify.sanitize(`[${name}] ${msg}`));
    })
  });
})

app.get("/transcript", async (req, res) => {
  res.send(DOMPurify.sanitize(chatMessages.join("<br>\n")));
})

app.post("/clearchat", async (req, res) => {
  chatMessages = [];
  res.send("chat cleared")
})

app.get('/register', async (req, res) => {
  res.render("register.ejs")
})

app.post('/register', async (req, res) => {
  const username = req.body.username;

  if (username && typeof username == 'string' && username.match(/^([a-z|A-Z|0-9])+$/g)) {
    const isUserTaken = await client.exists(username);
    if (isUserTaken) {
      return res.json({ "error": "Username is taken." });
    }
    else {
      await client.hSet(username, {'username': username, 'cash': 0});
      const token = await utils.createToken(username, client)
      return res.cookie("user", token, {httpOnly: true}).redirect(302, "/");
    }
  }
  res.json({ "error": "Username is invalid." });
})

app.get('/stats/:username', utils.authMiddleware, async (req, res) => {
  const username = req.params.username
  const userExists = await client.exists(username);
  if(!userExists){
    return res.send("user doesn't exist")
  }
  const stats = await client.hGetAll(username);
  return res.render("stats.ejs", { stats: stats })
})

app.post('/report/:username', utils.authMiddleware, async (req, res) => {
  let result;
  let username;
  if(req.user.username === "admin"){
    if(req.params.username !== "admin"){
      result = "User has been banned!";
    }else{
      result = process.env.FLAG;
    }
  }else{
    username = req.params.username;
    const userExists = await client.exists(username);
    if(!userExists){
      result = "User doesn't exist";
    }else if(username === "admin") {
      result = "You can't report the admin!"
    }
    else{
      bot.checkPage(`http://${nginxhost}:${nginxport}/stats/${username}`,client);
      result = "Admin is checking the page!"
    }
  }
  return res.redirect(302, `/?result=${result}`);
})

app.post('/logout', utils.authMiddleware, async (req, res) => {
  res.clearCookie('user');
  res.send("cleared cookies")
})

app.post('/win', utils.authMiddleware, async (req, res) => {
  const winnings = await client.hGetAll(req.user.username);
  await client.hSet(req.user.username, {username: req.user.username, cash: parseInt(winnings.cash)+100});

  res.send("Updated earnings");
})

app.listen(port, async function() {
  await client.hSet('admin', {'username': 'admin', cash: 100000000});
  npcs.forEach(async (name) => {
    await client.hSet(name, {'username': name, cash: Math.floor(Math.pow(Math.random()*1000,2))*100});
  })
});