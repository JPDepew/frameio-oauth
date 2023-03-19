from urllib.parse import urlencode
import uuid
from flask import Flask, redirect, request
import requests

app = Flask(__name__)

CLIENT_ID = "<client_id>"

AUTHORIZE_URL = "https://applications.frame.io/oauth2/auth"
TOKEN_URL = "https://applications.frame.io/oauth2/token"
# The scopes you've chosen for your app, space-delimited
SCOPE = (
  "offline asset.create reviewlink.read project.create asset.read "
  "project.read asset.update project.update account.read team.read asset.delete" 
)
# The callback URI for your app
REDIRECT_URI = "http://127.0.0.1:5000/callback/"


# Steps
# 1. User goes to the login url, which redirects to the auth url
# 2. User logs in, grants permissions
# 3. This redirects to the callback url, which is in the UI.
# Grabs query param (code, state?, scope?), makes post to backend,
# which returns access token and refresh token.
# 4. User can use theses to access frame.io stuff.


@app.route('/')
@app.route('/login/')
def hello():
    auth_url = create_auth_url()
    return redirect(auth_url)


@app.route('/callback/')
def about():
    state = request.args.get('state')
    scope = request.args.get('scope')
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return "Error: " + error

    # If using PKCE, you must include the CLIENT_ID in your request body  
    post_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": SCOPE,
        "client_id": CLIENT_ID 
    }

    # Send a POST request with the data you need to receive an access token. 
    # If everything goes well, it will be returned to you and you can use it with
    # Frame.io

    # If using PKCE, use the below request with no auth
    response = requests.post(TOKEN_URL, data=post_data) 
    # This is the data needed to access frame.io
    return response.text


def create_auth_url():
    credentials = {
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'scope': SCOPE,
        'state': str(uuid.uuid4())
    }
    url = (AUTHORIZE_URL + "?" + urlencode(credentials))
    print(url)
    return url


