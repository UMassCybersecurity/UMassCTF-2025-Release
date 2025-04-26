from flask import Flask, request, render_template, session, redirect, send_from_directory
from time import sleep
import shutil
import os
from base64 import b64decode

from FlashTemplater import FlashGameHelper
from server_helpers import ROLE_USER,ROLE_DEV,ROLE_ADMIN,APP_SECRET
from db import DatabaseHelper
from bot import visit_profile

app = Flask(__name__)
app.secret_key = APP_SECRET
app.jinja_env.filters['b64decode'] = lambda s: b64decode(s).decode()

while True:
    try: 
        database_helper = DatabaseHelper()
        break
    except Exception as e:
        print("Failed to connect to database. Sleeping then trying again.",flush=True)
        sleep(1)

@app.route("/")
def index():
    return render_template('index.html')

@app.get("/login")
def login_get():
    return render_template('login.html')

@app.post("/login")
def login_post():
    username = request.form.get('username', None)
    password = request.form.get('password', None)
    if(type(username) == str and type(password) == str):
        result = database_helper.loginUser(username,password)
        if(result != None and result[0] == username):
            user, role, uid = result
            session['username'] = user
            session['role'] = role
            session['uid'] = uid
            return redirect("/dev")
        return redirect("/login?message=Error:+Incorrect+Username+or+Password!")
    return redirect("/login?message=Error:+Malformed+Username+or+Password!")

@app.get("/register")
def register_get():
    return render_template('register.html')

@app.post("/register")
def register_post():
    username = request.form.get('username', None)
    password = request.form.get('password', None)
    if(type(username) == str and type(password) == str):
        result = database_helper.getUser(username)
        if(result):
            return redirect("/register?message=Error:+User+already+exists!")
        database_helper.registerUser(username,password,"This is a sample description.")
        username, user_desc, uid = database_helper.getUser(username)
        os.makedirs(os.path.dirname(f"users/{uid}.jpg"), exist_ok=True)
        shutil.copy("static/default_profile.jpg",f"users/{uid}.jpg")
        return redirect("/login?message=Success:+Registered+your+user!")
    return "Invalid username and/or password!"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect("/")

@app.get("/dev")
def dev_get():
    if('role' in session and 'username' in session):
        if(session['role'] == 2):
            games = database_helper.getGames(session['username'])
            return render_template('dev.html',games=games,username=session['username'])
        return render_template('dev.html',err="You are not a dev!",username=session['username'])
    return redirect("/login")

@app.get("/profile")
def profile_user_get():
    username = request.args.get('username',None)
    if('username' in session):
        if(username==None):
            return redirect(f'/profile?username={session["username"]}')
        if(session['username']==username or session['username']=='admin'):
            username,user_desc, uid = database_helper.getUser(username)
            return render_template('profile.html',username=username,user_desc=user_desc,uid=uid)
    return redirect("/login")

@app.post("/create_game")
def create_game():
    if('role' in session and session['role']==2):
        game_name = request.form.get('game_name', None)
        game_desc = request.form.get('game_desc', "")
        if(game_name==None):
            return "You must provide a game name",400
        code = FlashGameHelper.gen_game_from_template(game_name)
        database_helper.createGame(game_name,code,game_desc,session['username'])
        return redirect('/dev?message=Created+game+successfully!')
    return "You are not a dev!",403

@app.route("/request_access/<username>")
def request_access(username):
    visit_profile(username)
    return "Admin visited your profile but probably denied you!"

@app.route("/admit/<uid>")
def admit_user(uid):
    if('username' in session and 'role' in session):
        if(session['role'] == 3):
            database_helper.promoteUser(uid)
            return "Accepted.",200
        return "Only admin can accept people to the program.",403
    return "Unauthorized.",403

@app.route("/user/profile_pic/<username>")
def get_profile_pic(username):
    if('username' in session and session['username']==username):
        _, _, uid = database_helper.getUser(username)
        return send_from_directory('users', f'{uid}.jpg')
    return "Unauthorized.",403

@app.route("/game/<username>/<game_name>")
def get_dev_game(username,game_name):
    if('username' in session and session['username']==username):
        game_name, code = database_helper.getGame(username,game_name)
        return render_template("game.html",username=username,code=code,game_name=game_name)
    return "Unauthorized.",403

@app.route("/game/<username>/<game_name>/edit")
def edit_game(username,game_name):
    if('username' in session and session['username']==username):
        return "Editing is not supported right now.",501
    return "Unauthorized.",403

@app.route("/game/<username>/<game_name>/test")
def test_game(username,game_name):
    if('username' in session and session['username']==username):
        game_name, code = database_helper.getGame(username,game_name)
        return FlashGameHelper.test_game(code,game_name), 200
    return "Unauthorized.",403

@app.post("/profile/update")
def update_user():
    if('username' in session):
        user_desc = request.form.get('about_me', "")
        database_helper.updateUserDesc(session['username'],user_desc)
        return redirect("/profile")
    return "Unauthorized.",403