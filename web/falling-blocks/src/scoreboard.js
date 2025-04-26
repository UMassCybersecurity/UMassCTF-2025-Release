const redis = require('redis');
const client = redis.createClient({url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`});

(async () => {
    client.on('error', err => console.log('Redis Client Error', err));
    await client.connect()
})();

const addScore = async (score, username) => {
    await client.zAdd('scores', { score: score, value: username });
}

const getScore = async () => {
    return await client.zRangeWithScores('scores', 0, 10, { REV: true });
}

module.exports = {addScore, getScore};