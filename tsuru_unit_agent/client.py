import requests
import json


class Client(object):
    def __init__(self, url):
        self.url = url

    def get_envs(self, app):
        response = requests.get("{}/apps/{}/envs".format(self.url, app))
        return json.loads(response)
