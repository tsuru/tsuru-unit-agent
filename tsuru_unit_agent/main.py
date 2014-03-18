from tsuru_unit_agent import tasks
from tsuru_unit_agent.client import Client


def main():
    client = Client("http://localhost")
    envs = client.get_envs("app_name")
    tasks.save_apprc_file(envs)
    tasks.execute_start_script()
