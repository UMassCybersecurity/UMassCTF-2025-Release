import os
from flask import Flask, request, Response
import requests as r
import time

# using no static_url_path defaults to /static, which breaks the reverse proxy for /static
server = Flask(__name__, static_url_path="/dummy")
expiries = {}
contentTypes = {}
webport = os.environ['WEB_PORT']
webhost = os.environ["WEB_HOST"]

@server.route('/<path:path>')
@server.route('/', defaults={'path':''})
def staticcache(path=""):
    # cache file if it's in /static
    if path.split("/")[0] == "static":
        path = path.split("/", 1)[1]
        filepath = os.path.normpath(f"cache/{path}") if path else "cache/index"
        
        if os.path.isfile(filepath):
            if filepath in expiries and time.time() <= expiries[filepath]+15:
                with open(filepath, 'rb') as file:
                    response = Response(file.read(), 200, [("Content-Type", contentTypes[filepath])])
                    return response


        req = f"http://{webhost}:{webport}/static/{path}"
        resp = r.get(req, data=request.get_data(), headers=request.headers)

        with open(filepath, 'wb') as file:
            expiry = time.time()
            expiries[filepath] = expiry
            contentTypes[filepath] = resp.raw.headers["Content-Type"]
            file.write(resp.content)

        response = Response(resp.content, resp.status_code, [("Content-Type", contentTypes[filepath])])
        return response

    # simply pass req through and respond with the same headers
    resp = r.get(f"http://{webhost}:{webport}/{path}", data=request.get_data(), headers=request.headers, allow_redirects=False)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in     resp.raw.headers.items() if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response

@server.route('/', defaults={'path':''}, methods=["POST"])
@server.route('/<path:path>', methods=["POST"])
def rootpost(path=""):
    # simply pass req through and respond with the same headers
    resp = r.post(f"http://{webhost}:{webport}/{path}", data=request.get_data(), headers=request.headers, allow_redirects=False)
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in     resp.raw.headers.items() if name.lower() not in excluded_headers]
    response = Response(resp.content, resp.status_code, headers)
    return response

    
if __name__ == '__main__':
    server.run(debug=False)
