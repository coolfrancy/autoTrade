import os
from dotenv import load_dotenv
import requests

load_dotenv()
ACC_ACCESS_TOKEN = os.getenv("ACC_ACCESS_TOKEN")

url = "https://api.schwabapi.com/trader/v1/accounts"
headers = {
    "Authorization": f"Bearer {ACC_ACCESS_TOKEN}"
}


resp = requests.get(url, headers=headers, timeout=30)
resp.raise_for_status()
accounts = resp.json()
print(accounts)
