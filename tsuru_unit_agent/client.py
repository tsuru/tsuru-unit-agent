import requests
import json


class Client(object):
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def get_envs(self, app):
        response = requests.get(
            "{}/apps/{}/env".format(self.url, app),
            headers={"Authorization", "bearer {}".format(self.token)})
        return json.loads(response)
