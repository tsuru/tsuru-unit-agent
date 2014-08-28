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
    def test_register_unit(self, post_mock):
        response = mock.Mock()
        response.json = mock.Mock(side_effect=lambda: {"a": "b"})
        post_mock.return_value = response
        client = Client("http://localhost", "token")
        envs = client.register_unit(app="myapp")
        self.assertDictEqual(envs, {"a": "b"})
        post_mock.assert_called_with(
            "{}/apps/myapp/units/register".format(client.url),
            data={"hostname": gethostname()},
            headers={"Authorization": "bearer token"})

    @mock.patch("requests.post")
    def test_post_app_yaml(self, post_mock):
        response = mock.Mock()
        response.status_code = 200
        post_mock.return_value = response
        client = Client("http://localhost", "token")
        client.post_app_yaml(app="myapp", data=[{"x": "y"}])
        post_mock.assert_called_with(
            "{}/apps/myapp/customdata".format(client.url),
            data='[{"x": "y"}]',
            headers={
                "Authorization": "bearer token",
                "Content-Type": "application/json",
            })
