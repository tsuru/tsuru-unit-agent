import unittest
import mock

from tsuru_unit_agent.client import Client


class TestClient(unittest.TestCase):
    def test_client(self):
        client = Client(url="http://localhost")
        self.assertEqual(client.url, "http://localhost")

    @mock.patch("requests.get")
    def test_get_envs(self, get_mock):
        get_mock.return_value = "{}"
        client = Client(url="http://localhost")
        envs = client.get_envs(app="myapp")
        self.assertDictEqual(envs, {})
        get_mock.assert_called_with(
            "{}/apps/myapp/envs".format(client.url))
