const express = require('express');
const { v4: uuidv4 } = require('uuid');
const path = require('path');
const cookiep = require('cookie-parser');
const bodyp = require('body-parser');

const fs = require('fs');

const redis = require('redis');
const admin = require('./admin.js');

const app = express();
const port = 3000;
const banned_fetch_dests = ['iframe', 'embed', 'object'];

const client = redis.createClient({
  'url': process.env.REDIS_URL
})
client.on('error', err => console.log('Redis Client Error', err));
client.connect();

app.use(cookiep());
app.use(bodyp.urlencoded())
app.use('/images', express.static('images'));

async function set_cache(key,val){
  return (await client.set(key,JSON.stringify(val), 'EX', 3600));
}

async function get_cache(key){
  return JSON.parse(await client.get(key));
}

app.get('/', async (req, res) => {
  let UID;
  if(!req.cookies || !req.cookies.user || !(await client.exists(req.cookies.user))){
    UID = uuidv4();
    await set_cache(UID,["This is my first note!"]);
    await set_cache(UID + "_cust",0);
    res.set({'Set-Cookie':`user=${UID}`});
  } else {
    UID = req.cookies.user;
  }
  res.redirect(`/user/${UID}`);
})

app.get('/user/:id',async (req,res)=>{
  if(!req.params || !(await client.exists(req.params.id))){

    return res.redirect('/')
  }

  let notes = await get_cache(req.params.id);

  if(req.params.id.includes("admin") && req.ip != '::ffff:127.0.0.1'){
    return res.send("You're not an admin!");
  } else if (req.params.id.includes("admin") && req.ip == '::ffff:127.0.0.1' && !banned_fetch_dests.includes(req.headers['sec-fetch-dest'])) {
    res.cookie('x', process.env.FLAG);
  }

  res.setHeader('Content-Type', 'text/html');

  const customers = await get_cache(req.params.id + "_cust") + 1;
  await set_cache(req.params.id + "_cust", customers);

  let htmlContent;
  fs.readFile(path.join(__dirname,'public','index.html'), (err, data) => {
    if(err) {
      res.send("Problem creating HTML");
    } else {
      htmlContent = data.toString();

      let content = '<div id="notes">';

      notes.forEach(note => {
        content += "<li>";
        content += note;
        content += "</li>";
      })

      content += '</div>';
      htmlContent = htmlContent.replace('<div id="notes"> </div>', content);
      htmlContent = htmlContent.replace('<div id="customers"> </div>', `<div id="customers"> Customer Count: ${customers}</div>`);

      res.send(htmlContent);
    }
  });
})

app.get('/report/:id',async (req,res)=>{
  admin_uid = uuidv4() + "-admin";
  res.send("I'm reviewing your notes! My ID is " + admin_uid);
  await set_cache(admin_uid,["Remember to rember not to forgor my notes"]);
  try {
    await admin(admin_uid, req.params.id);
  } catch (e) {
    res.send("Admin ran into issues!");
  }
})

app.get('/clear',async (req,res)=>{
  if(!req.cookies || !req.cookies.user || !(await client.exists(req.cookies.user))){
    return res.send("Hmm are you even a user? Go to /");
  }

  if(req.cookies.user && req.cookies.user.includes("admin") && req.ip != '::ffff:127.0.0.1'){
    return res.send("You're not an admin!")
  }

  await set_cache(req.cookies.user,[]);
  await set_cache(req.cookies.user + "_cust", 0);

  return res.redirect(`/user/${req.cookies.user}`);
})

app.get('/create',async (req,res)=>{
  if(!req.cookies || !req.cookies.user || !(await client.exists(req.cookies.user))){
    return res.send("Hmm are you even a user? Go to /");
  }

  if(!req.query.note){
    return res.send("Did not get a note")
  }

  if(req.cookies.user.includes("admin") && req.ip != '::ffff:127.0.0.1'){
    return res.send("You're not an admin!")
  }

  // I get to have longer notes!
  if(req.ip === '::ffff:127.0.0.1'){
    if(req.query.note.length > 56) {
      return res.send("Invalid note length!")
    }
  } else {
    if(req.query.note.length > 16) {
      return res.send("Invalid note length!")
    }
  }

  let user_note = await get_cache(req.cookies.user);

  if(!user_note) {
    return res.send("Problem while fetching notes! Try something else perhaps?")
  }

  user_note.push(req.query.note);

  await set_cache(req.cookies.user,user_note);

  return res.send("Note uploaded!")
})

app.post('/create',async (req,res)=>{
  if(!req.cookies || !req.cookies.user || !(client.exists(req.cookies.user))){
    return res.send("Hmm are you even a user? Go to /");
  }
  if(!req.body.note){
    return res.send("Did not get a note body")
  }

  if(req.cookies.user.includes("admin") && req.ip != '::ffff:127.0.0.1'){
    return res.send("You're not an admin!")
  }

  // I get to have longer notes!
  if(req.ip === '::ffff:127.0.0.1'){
    if(req.body.note.length > 56) {
      return res.send("Invalid note length!")
    }
  } else {
    if(req.body.note.length > 16) {
      return res.send("Invalid note length!")
    }
  }

  let user_note = await get_cache(req.cookies.user);

  if(!user_note) {
    return res.send("Problem while fetching notes! Try something else perhaps?")
  }

  user_note.push(req.body.note);
  await set_cache(req.cookies.user,user_note);
  return res.redirect(`/user/${req.cookies.user}`);
})

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})
