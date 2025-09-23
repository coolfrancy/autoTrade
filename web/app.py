from flask import Flask, request
import os, base64, requests
from dotenv import load_dotenv
from urllib.parse import unquote

#initialize flask app
app = Flask(__name__)

#get env variables
load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

TOKEN_URL   = "https://api.schwabapi.com/v1/oauth/token"
REDIRECT_URI = "https://autotrade-production-2561.up.railway.app/"


@app.route("/", methods=["GET"])
def callback_root():
    qCode = request.args.get("code")

    if not qCode:
        return "No ?code=... in query string", 400

    code = unquote(qCode)
    basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    resp = requests.post(
        TOKEN_URL,
        headers={
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": code,                     # ONLY the code value, no "&session=..."
            "redirect_uri": REDIRECT_URI,     # exact string as registered
        },
        timeout=30,
    )

    return resp.json()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
