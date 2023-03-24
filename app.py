import json
import math
from urllib.parse import urlencode
import uuid
from flask import Flask, redirect, render_template, request
import requests
from frameioclient import FrameioClient

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

TOKEN = ""
REFRESH_TOKEN = ""


# Steps
# 1. User goes to the login url, which redirects to the auth url
# 2. User logs in, grants permissions
# 3. This redirects to the callback url, which is in the UI.
# Grabs query param (code, state?, scope?), makes post to backend,
# which returns access token and refresh token.
# 4. User can use these to access frame.io stuff.


@app.route('/')
@app.route('/login/')
def index():
    auth_url = create_auth_url()
    return redirect(auth_url)


@app.route('/callback/')
def callback():
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
    resp = requests.post(TOKEN_URL, data=post_data)
    response_data = resp.json()
    print(response_data)
    global TOKEN
    global REFRESH_TOKEN
    TOKEN = response_data["access_token"]
    REFRESH_TOKEN = response_data["refresh_token"]
    # This is the data needed to access frame.io
    return render_template("home.html", token=TOKEN)


@app.route('/projects/')
def get_projects():
    token = request.args.get("token")
    resp = make_frameio_request("accounts", token=token)
    account_id = resp.json()[0]["id"]
    resp = make_frameio_request(f"accounts/{account_id}/teams", token=token)
    team_id = resp.json()[0]["id"]
    resp = make_frameio_request(f"teams/{team_id}/projects", token=token)
    root_asset_id = resp.json()[0]["root_asset_id"]
    resp = make_frameio_request(f"assets/{root_asset_id}/children?type=folder", token=token)

    folder_names = []
    for folder in resp.json():
        folder_id = folder["id"]
        resp = make_frameio_request(f"assets/{folder_id}/children?type=folder", token=token)
        folder_names.append({"name": folder["name"], "id": folder_id})

    return folder_names


@app.route("/upload_video/", methods=["POST"])
def upload_video():
    folder_id = "89fd3673-4fee-4e22-8c60-957967e23b06"
    token = request.args.get("token")
    data = request.files
    file = data["video"]
    filesize = len(file.read())
    client = FrameioClient(token)
    asset = client.assets.create(
        parent_asset_id=folder_id,
        name=file.filename,
        type="file",
        filetype="video/quicktime",
        filesize=filesize,
    )

    chunk_size = math.ceil(float(filesize) / float(len(asset["upload_urls"])))
    file.seek(0)
    for url in asset["upload_urls"]:
        chunk = file.read(chunk_size)
        resp = requests.put(
            url,
            chunk,
            headers={
                "Content-Type": "video/quicktime",
                "x-amz-acl": "private",
            }
        )
        print(resp)
    return {"message": "ok"}


def create_auth_url():
    credentials = {
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'scope': SCOPE,
        'state': str(uuid.uuid4())
    }
    url = (AUTHORIZE_URL + "?" + urlencode(credentials))
    return url


def make_frameio_request(path: str, method: str = "GET", token=TOKEN, data=None) -> requests.Response:
    headers = {"Authorization": f"Bearer {token}"}
    return requests.request(
        method,
        f"https://api.frame.io/v2/{path}",
        headers=headers,
        data=data
    )

