const puppeteer = require('puppeteer');
const env = require('dotenv').config();
function getSub(admin_uid, user){
  admin_uid = admin_uid + "";
  return new Promise(async (res,rej)=>{
    const browser = await puppeteer.launch({
      executablePath: '/usr/bin/google-chrome-stable',
      args: ['--no-sandbox']
    });
    let page = await browser.newPage();
    await page.setCookie(...[{
      'name':'user',
      'value':admin_uid,
      'url':'http://127.0.0.1'
    }]);
    await page.setRequestInterception(true);

    page.on('request', (request) => {
      if (!request.url().startsWith("http://127.0.0.1:3000")) {
        request.abort();
      } else {
        request.continue();
      }
    });

    // For debugging
    // page
    //   .on('console', message =>
    //   {
    //     console.log(`[BROWSER] ${message.type().substr(0, 3).toUpperCase()} ${message.location().url} ${message.text()}`);
    //   })
    //   .on('pageerror', ({ message }) => console.log(message))
    //   .on('response', response =>
    //     {
    //     console.log(`[BROWSER] ${response.status()} ${response.url()}`);
    //
    //     })
    //   .on('requestfailed', request =>
    //   console.log(`[BROWSER] ${request.failure()} ${request.url()}`))

    try {
      await page.goto(`http://127.0.0.1:${3000}/user/${user}`);
      await new Promise((resolve) => setTimeout(resolve, 5*60*1000));
    } finally {
      return res(await browser.close());
    }
  })
}

module.exports = getSub
