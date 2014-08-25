import unittest
import mock
from socket import gethostname

from tsuru_unit_agent.client import Client


class TestClient(unittest.TestCase):
    def test_client(self):
        client = Client("http://localhost", "token")
        self.assertEqual(client.url, "http://localhost")
        self.assertEqual(client.token, "token")

    @mock.patch("requests.post")
    def test_get_envs(self, post_mock):
        response = mock.Mock()
        response.json = mock.Mock(side_effect=lambda: {"a": "b"})
        post_mock.return_value = response
        client = Client("http://localhost", "token")
        envs = client.get_envs(app="myapp")
        self.assertDictEqual(envs, {"a": "b"})
        post_mock.assert_called_with(
            "{}/apps/myapp/units/register".format(client.url),
            data={"hostname": gethostname()},
            headers={"Authorization": "bearer token"})
