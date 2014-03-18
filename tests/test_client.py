import unittest

from tsuru_unit_agent.client import Client


class TestClient(unittest.TestCase):
    def test_client(self):
        client = Client(url="http://localhost")
        self.assertEqual(client.url, "http://localhost")
