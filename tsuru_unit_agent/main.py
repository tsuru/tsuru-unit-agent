import argparse
import os
import sys

import semantic_version

from requests.exceptions import ConnectionError

from tsuru_unit_agent import heartbeat, tasks
from tsuru_unit_agent.client import Client

TEMP_ENV_FILE = "/tmp/app_envs"


def run_action(args):
    client = Client(args.url, args.token)
    envs = None
    try:
        envs, supported_tsuru = client.register_unit(args.app_name)
        save_apprc_file(envs, supported_tsuru)
    except ConnectionError:
        envs = tasks.parse_apprc_file()
    yaml_data = tasks.load_app_yaml()
    tasks.write_circus_conf(envs=envs)
    tasks.run_restart_hooks('before', yaml_data, envs=envs)
    tasks.execute_start_script(args.start_cmd, envs=envs, with_shell=False)
    tasks.run_restart_hooks('after', yaml_data, envs=envs)
    remove_temp_env_file()


def deploy_action(args):
    heartbeat.StderrHeartbeat().start()
    client = Client(args.url, args.token)
    envs, supported_tsuru = client.register_unit(args.app_name)
    save_apprc_file(envs, supported_tsuru)
    tasks.execute_start_script(args.start_cmd)
    yaml_data = tasks.load_app_yaml()
    client.post_app_yaml(args.app_name, yaml_data)
    tasks.run_build_hooks(yaml_data, envs=envs)
    remove_temp_env_file()
    yaml_data["procfile"] = tasks.load_procfile()
    yaml_data["processes"] = tasks.parse_procfile()
    client.register_unit(args.app_name, yaml_data)
    tasks.write_circus_conf(envs=envs)


def save_apprc_file(envs, supported_tsuru):
    no_apprc_version = semantic_version.Version("0.17.0")
    supported_version = semantic_version.Version(supported_tsuru)
    port_envs = {"port": "8888", "PORT": "8888"}
    if supported_version < no_apprc_version:
        tasks.save_apprc_file(envs)
    else:
        tasks.save_apprc_file(port_envs)
        tasks.save_apprc_file(envs, file_path=TEMP_ENV_FILE)


def remove_temp_env_file():
    try:
        os.unlink(TEMP_ENV_FILE)
    except OSError:
        pass


actions = {
    'run': run_action,
    'deploy': deploy_action
}


def parse_args(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(description='Runs tsuru-unit-agent.')
    parser.add_argument('url', help='URL for tsuru API server')
    parser.add_argument('token', help='Authentication token for tsuru API server')
    parser.add_argument('app_name', help='The app name')
    parser.add_argument('start_cmd', help='Command to run after notifying tsuru API server')
    parser.add_argument('action', default='run', nargs='?', choices=actions.keys(), help='Action being executed')
    return parser.parse_args(args)


def main():
    args = parse_args()
    actions[args.action](args)


if __name__ == '__main__':
    main()
