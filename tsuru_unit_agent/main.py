import sys

from tsuru_unit_agent import tasks
from tsuru_unit_agent.client import Client


def main(url, token, app_name):
    client = Client(url, token)
    envs = client.get_envs(app_name)
    tasks.save_apprc_file(envs)
    tasks.execute_start_script()


if __name__ == "__main__":
    url = sys.argv[1]
    token = sys.argv[2]
    app_name = sys.argv[3]
    main(url, token, app_name)
