from selenium import webdriver
from time import sleep
from server_helpers import APP_SECRET
from flask.sessions import SecureCookieSessionInterface

# Code for creating admin session keys lifted from https://github.com/noraj/flask-session-cookie-manager/blob/master/flask_session_cookie_manager3.py 
class MockApp(object):
    def __init__(self):
        self.secret_key = APP_SECRET
        self.config = {"SECRET_KEY_FALLBACKS" : None}

def visit_profile(username):
    options = webdriver.ChromeOptions()
    options.add_argument("no-sandbox")
    options.add_argument("headless")
    options.add_argument("disable-gpu")
    driver = webdriver.Chrome(options=options)
    # Create admin flask session manually
    si = SecureCookieSessionInterface()
    app = MockApp()
    s = si.get_signing_serializer(app)
    ADMIN_COOKIE = s.dumps({'username':'admin','role':3})
    driver.get("http://localhost")
    driver.add_cookie({"name": "session", "value": ADMIN_COOKIE})
    driver.get(f"http://localhost/profile?username={username}")
    # Access requests via the `requests` attribute
    sleep(3)
    driver.close()