const puppeteer = require('puppeteer');
const utils = require('./util.js')

const nginxhost = process.env.NGINX_HOST;

function checkPage(path, client) {
    return new Promise(async (res, rej) => {
        const browser = await puppeteer.launch({
            executablePath: '/usr/bin/chromium',
            headless: true,
            pipe: true,
            args: ['--no-sandbox','--disable-gpu']
        });
        try {
            const page = await browser.newPage();
            const token = await utils.createToken('admin', client);
            await page.setCookie({
                name: 'user',
                value: token,
                domain: nginxhost,
                httpOnly: true
            });
            await page.goto(path,{
                timeout: 3000
            });
            await new Promise(r => setTimeout(r, 3000));
        }
        catch(e){
            console.log(e);
        } finally {
            await browser.close();
        }
    })
}

module.exports = { checkPage };