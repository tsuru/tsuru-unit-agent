from socket import gethostname
import json

import requests


class Client(object):
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def register_unit(self, app):
        params = {
            'headers': {"Authorization": "bearer {}".format(self.token)},
        }
        response = requests.post(
            "{}/apps/{}/units/register".format(self.url, app),
            data={"hostname": gethostname()},
            **params)
        if response.status_code != 200:
            response = requests.get(
                "{}/apps/{}/env".format(self.url, app),
                **params)
        return response.json()

    def post_app_yaml(self, app, data):
        response = requests.post(
            "{}/apps/{}/customdata".format(self.url, app),
            data=json.dumps(data),
            headers={
                "Authorization": "bearer {}".format(self.token),
                "Content-Type": "application/json",
            })
        if not 200 <= response.status_code < 400:
            raise Exception("invalid response {} - {}".format(response.status_code, response.text))
