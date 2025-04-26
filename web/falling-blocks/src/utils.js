const jwt = require('jsonwebtoken');


const parseUser = (userString) => {
    let userObj = JSON.parse(userString);
    userObj.tokens = parseFloat(userObj.tokens);
    return userObj;
}

const createToken = async (username,client) =>{
    let user = await client.HGETALL(username);
    user.username = username;
    user.tokens = user.tokens.toString();
    await client.HSET(username, "tokens", jwt.sign(user,process.env.SECRET_TOKEN));
}

const authMiddleware = (req, res, next) => {
    try {
        if (req.cookies.user) {
            try {
                req.user = jwt.verify(req.cookies['user'], process.env.SECRET_TOKEN);
                req.user.tokens = parseFloat(req.user.tokens);
                return next();
            }
            catch (e) {
                console.log(e);
                return res.send("Invalid JWT, try registering a new token.");
            }
        }
        return res.send("Error when processing JWT.");
    } catch (err) {
        console.error('Error:', err);
    }
}

module.exports = {createToken,parseUser,authMiddleware};