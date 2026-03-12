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


class TestBodyForwarding(unittest.TestCase):
    def _make_handler(self, method, path, body_bytes):
        handler = srv.ProxyHandler.__new__(srv.ProxyHandler)
        handler.command = method
        handler.path = path
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body_bytes)),
        }
        handler.rfile = MagicMock()
        handler.rfile.read.return_value = body_bytes
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        return handler

    @patch("urllib.request.urlopen")
    def test_post_forwards_body(self, mock_urlopen):
        body = b'{"name": "Test Workout"}'
        mock_resp = MagicMock()
        mock_resp.status = 201
        mock_resp.read.return_value = b'{"id": "e456"}'
        mock_resp.headers.get.return_value = "application/json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        handler = self._make_handler("POST", "/api/v1/athlete/i123/events", body)
        handler.do_POST()

        call_args = mock_urlopen.call_args[0][0]
        self.assertEqual(call_args.data, body)
        self.assertEqual(call_args.get_method(), "POST")
        handler.send_response.assert_called_with(201)

    @patch("urllib.request.urlopen")
    def test_delete_sends_no_body(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 204
        mock_resp.read.return_value = b""
        mock_resp.headers.get.return_value = "application/json"
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        handler = srv.ProxyHandler.__new__(srv.ProxyHandler)
        handler.command = "DELETE"
        handler.path = "/api/v1/athlete/i123/events/e456"
        handler.headers = {}
        handler.wfile = MagicMock()
        handler.send_response = MagicMock()
        handler.send_header = MagicMock()
        handler.end_headers = MagicMock()
        handler.do_DELETE()

        call_args = mock_urlopen.call_args[0][0]
        self.assertIsNone(call_args.data)


if __name__ == "__main__":
    unittest.main()
