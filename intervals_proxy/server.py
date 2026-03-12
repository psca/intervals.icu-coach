import base64
import http.server
import os
import urllib.error
import urllib.request

API_KEY = os.environ["INTERVALS_API_KEY"]
BASE_URL = "https://api.intervals.icu"
PORT = int(os.environ.get("INTERVALS_PROXY_PORT", 8080))
AUTH = "Basic " + base64.b64encode(f"API_KEY:{API_KEY}".encode()).decode()
