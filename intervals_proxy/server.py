import base64
import http.server
import os
import urllib.error
import urllib.request

API_KEY = os.environ["INTERVALS_API_KEY"]
BASE_URL = "https://api.intervals.icu"
PORT = int(os.environ.get("INTERVALS_PROXY_PORT", 8080))
AUTH = "Basic " + base64.b64encode(f"API_KEY:{API_KEY}".encode()).decode()


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def _proxy(self, body=None):
        url = BASE_URL + self.path
        req = urllib.request.Request(
            url,
            data=body,
            method=self.command,
            headers={
                "Authorization": AUTH,
                "Accept": "application/json",
                "Content-Type": self.headers.get("Content-Type", "application/json"),
            },
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = resp.read()
                self.send_response(resp.status)
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            data = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else None

    def do_GET(self):
        self._proxy()

    def do_POST(self):
        self._proxy(self._read_body())

    def do_PUT(self):
        self._proxy(self._read_body())

    def do_DELETE(self):
        self._proxy()

    def do_PATCH(self):
        self._proxy(self._read_body())

    def log_message(self, format, *args):
        pass
