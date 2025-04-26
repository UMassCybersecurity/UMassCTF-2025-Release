const jwt = require('jsonwebtoken');


const createToken = async (username,client) =>{
  let user = await client.hGetAll(username);
  return jwt.sign(user,process.env.SECRET_TOKEN);
}

const authMiddleware = (req, res, next) => {
    if (req.cookies && req.cookies.user) {
        try {
            req.user = jwt.verify(req.cookies['user'], process.env.SECRET_TOKEN);
            delete req.user['iat'];
            return next();
        }
        catch (e) {
            console.log(e);
            return res.send("Invalid JWT, try registering a new token.");
        }
    }
    return res.send("Error when processing JWT.");
}

const indexMiddleware = (req, res, next) => {
    if (req.cookies && req.cookies.user) {
        try {
            req.user = jwt.verify(req.cookies['user'], process.env.SECRET_TOKEN);
            delete req.user['iat'];
            return next();
        }
        catch (e) {
            console.log(e);
            return res.redirect(302, "/register")
        }
    }
    return res.redirect(302, "/register")
}

const authMiddlewareWS = async (ws, keys) => {
    try {
        const auth = await ws.nextMessage({ timeout: 3000 });
        const username = keys["" + auth.data]
        delete keys[""+auth.data]
        return username;
    }
    catch (e) {
        console.log(e);
        ws.send("Invalid key");
        ws.close();
        return false;
    }
}

module.exports = {authMiddleware,authMiddlewareWS,createToken,indexMiddleware};