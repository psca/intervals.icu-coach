import base64
import os
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

# Set env before importing server
os.environ["INTERVALS_API_KEY"] = "testkey123"
os.environ["INTERVALS_PROXY_PORT"] = "18080"

import intervals_proxy.server as srv


def _expected_auth():
    return "Basic " + base64.b64encode(b"API_KEY:testkey123").decode()


class TestAuthHeader(unittest.TestCase):
    def test_auth_value(self):
        self.assertEqual(srv.AUTH, _expected_auth())

    def test_auth_uses_api_key_username(self):
        decoded = base64.b64decode(srv.AUTH.split(" ")[1]).decode()
        username, password = decoded.split(":", 1)
        self.assertEqual(username, "API_KEY")
        self.assertEqual(password, "testkey123")


class TestGetForwarding(unittest.TestCase):
    def _make_handler(self, path):
        """Create a ProxyHandler instance with a mocked request."""
        handler = srv.ProxyHandler.__new__(srv.ProxyHandler)
        handler.command = "GET"
        handler.path = path
        handler.headers = {}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        return handler

    @patch("urllib.request.urlopen")
    def test_get_forwards_to_base_url(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"id": "i123"}'
        mock_resp.headers.get.return_value = "application/json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        handler = self._make_handler("/api/v1/activity/i123")
        handler.do_GET()

        call_args = mock_urlopen.call_args[0][0]
        self.assertEqual(call_args.full_url, "https://api.intervals.icu/api/v1/activity/i123")
        self.assertEqual(call_args.get_header("Authorization"), _expected_auth())
        handler.send_response.assert_called_with(200)

    @patch("urllib.request.urlopen")
    def test_get_passes_through_404(self, mock_urlopen):
        err = urllib.error.HTTPError(
            url="https://api.intervals.icu/api/v1/activity/bad",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=MagicMock(read=lambda: b'{"error":"not found"}'),
        )
        mock_urlopen.side_effect = err

        handler = self._make_handler("/api/v1/activity/bad")
        handler.do_GET()

        handler.send_response.assert_called_with(404)


if __name__ == "__main__":
    unittest.main()
