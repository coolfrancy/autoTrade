import requests
import base64
import requests
from urllib.parse import unquote


TOKEN_URL   = "https://api.schwabapi.com/v1/oauth/token"
REDIRECT_URI = "https://autotrade-production-2561.up.railway.app/"  # must match portal exactly
CLIENT_ID    = "cEgE4lrkL8AobSvVITK9RqgnX8nGAblVKV4b53WALa6AVDhN"
CLIENT_SECRET= "ZbhsB1tZglPD6bdL4ykJNIvj6XxiVTiaSPDIwBqgGD5zbKnuFnhpivXQAj1vCmkO"


code = unquote("C0.b2F1dGgyLmJkYy5zY2h3YWIuY29t.JpHK6zEu5sOdps3z26NUINlIFWdfIt5tLsgDG0Ag-1c%40")                 # converts %40 -> "@"

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

print(resp.status_code, resp.text)
