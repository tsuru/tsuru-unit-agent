import os

from tsuru_unit_agent import tasks
from tsuru_unit_agent.client import Client


def main():
    token = os.environ.get("TSURU_TOKEN")
    url = os.environ.get("TSURU_URL")
    app_name = os.environ.get("APPNAME")
    client = Client(url, token)
    envs = client.get_envs(app_name)
    tasks.save_apprc_file(envs)
    tasks.execute_start_script()
