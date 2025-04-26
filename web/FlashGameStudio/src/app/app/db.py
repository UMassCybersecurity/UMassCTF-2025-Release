import psycopg2
import os
from server_helpers import ROLE_USER, ROLE_DEV

class DatabaseHelper:
    def __init__(self):
        self.conn = psycopg2.connect(database="flashgamestudio",
            host=os.environ["POSTGRES_HOST"],
            user="postgres",
            password=os.environ["POSTGRES_PASSWORD"])
    
    def reset_conn(self):
        del self.conn
        self.conn = psycopg2.connect(database="flashgamestudio",
            host=os.environ["POSTGRES_HOST"],
            user="postgres",
            password=os.environ["POSTGRES_PASSWORD"])
        
    def getUsers(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM users;")
        return cur.fetchall()
    
    def loginUser(self,username,password):
        cur = self.conn.cursor()
        cur.execute("SELECT username,role_id,uid FROM users WHERE username=%s AND password=%s",(username,password))
        user = cur.fetchone()
        cur.close()
        return user
    
    def promoteUser(self,uid):
        cur = self.conn.cursor()
        try:
            cur.execute("UPDATE users SET role_id=%s WHERE uid=%s;",(ROLE_DEV,uid))
            self.conn.commit()
            cur.close()
        except:
            self.reset_conn()

    def updateUserDesc(self,username,user_desc):
        cur = self.conn.cursor()
        try:
            cur.execute("UPDATE users SET user_desc=%s WHERE username=%s;",(user_desc,username))
            self.conn.commit()
            cur.close()
        except:
            self.reset_conn()

    def registerUser(self,username,password,user_desc):
        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO USERS VALUES(uuid_generate_v4(),%s,%s,%s,%s);",(username,password,user_desc,ROLE_USER))
            self.conn.commit()
            cur.close()
        except:
            self.reset_conn()

    def getUser(self, username):
        cur = self.conn.cursor()
        cur.execute("SELECT username,user_desc,uid FROM users WHERE username=%s",(username,))
        user = cur.fetchone()
        cur.close()
        return user
    
    def getGames(self,username):
        cur = self.conn.cursor()
        cur.execute("SELECT game_name,game_desc,code FROM games WHERE username=%s",(username,))
        games = cur.fetchall()
        cur.close()
        return games
    
    def getGame(self,username,game_name):
        cur = self.conn.cursor()
        cur.execute("SELECT game_name,code FROM games WHERE username=%s AND game_name=%s",(username,game_name))
        game = cur.fetchone()
        cur.close()
        return game
    
    def createGame(self,game_name,game_code,game_desc,username):
        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO games VALUES(%s,%s,%s,%s);",(game_code,game_name,game_desc,username))
            self.conn.commit()
            cur.close()
        except:
            self.reset_conn()
            
