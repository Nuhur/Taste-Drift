import os
import requests
from dotenv import load_dotenv

print("script started")

load_dotenv()

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")


response = requests.post(
    "https://accounts.spotify.com/api/token",
    data={"grant_type": "client_credentials"},
    auth=(client_id, client_secret),
)

if response.status_code == 200:
    print("Success! Got a token.")
    print(response.json())
else:
    print(f"Failed with status {response.status_code}")
    print(response.text)