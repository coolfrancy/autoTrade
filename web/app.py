from flask import Flask, request
import os
from dotenv import load_dotenv
import requests

#initialize flask app
app = Flask(__name__)

#get env variables
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

@app.route("/", methods=["GET"])
def callback_root():
    code = request.args.get("code")
    if not code:
        return "No ?code=... in query string", 400


    resp = requests.post(
        "https://api.schwabapi.com/v1/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": "https://autotrade-production-2561.up.railway.app/",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=30,
    )
    return resp.json()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
