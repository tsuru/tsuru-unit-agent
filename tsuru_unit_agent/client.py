from socket import gethostname

import requests


class Client(object):
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def get_envs(self, app):
        response = requests.post(
            "{}/apps/{}/units/register".format(self.url, app),
            data={"hostname": gethostname()},
            headers={"Authorization": "bearer {}".format(self.token)})
        return response.json()
