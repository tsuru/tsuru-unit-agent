from socket import gethostname
import json

import requests


class Client(object):
    def __init__(self, url, token):
        self.url = url
        self.token = token

    def register_unit(self, app, custom_data=None):
        params = {
            'headers': {"Authorization": "bearer {}".format(self.token)},
        }
        request_data = {
            "hostname": gethostname(),
        }
        if custom_data is not None:
            request_data["customdata"] = json.dumps(custom_data)
        response = requests.post(
            "{}/apps/{}/units/register".format(self.url, app),
            data=request_data,
            **params)
        if 400 <= response.status_code < 500:
            response = requests.get(
                "{}/apps/{}/env".format(self.url, app),
                **params)
        if not 200 <= response.status_code < 400:
            raise Exception("invalid response {} - {}".format(response.status_code, response.text))
        tsuru_envs = response.json()
        envs = {env['name']: env['value'] for env in tsuru_envs}
        # TODO(fss): tsuru should handle this, see
        # https://github.com/tsuru/tsuru/issues/995.
        envs["port"] = envs["PORT"] = "8888"
        return envs

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
