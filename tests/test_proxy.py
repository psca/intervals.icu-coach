import base64
import os
import unittest
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


if __name__ == "__main__":
    unittest.main()
