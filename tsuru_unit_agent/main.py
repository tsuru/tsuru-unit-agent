import sys
import argparse
from requests.exceptions import ConnectionError

from tsuru_unit_agent import heartbeat, tasks
from tsuru_unit_agent.client import Client


def run_action(args):
    client = Client(args.url, args.token)
    envs = None
    try:
        envs = client.register_unit(args.app_name)
        tasks.save_apprc_file(envs)
    except ConnectionError:
        envs = tasks.parse_apprc_file()
    yaml_data = tasks.load_app_yaml()
    tasks.write_circus_conf(envs=envs)
    tasks.run_restart_hooks('before', yaml_data, envs=envs)
    tasks.execute_start_script(args.start_cmd, envs=envs, with_shell=False)
    tasks.run_restart_hooks('after', yaml_data, envs=envs)


def deploy_action(args):
    heartbeat.StderrHeartbeat().start()
    client = Client(args.url, args.token)
    envs = client.register_unit(args.app_name)
    tasks.save_apprc_file(envs)
    tasks.execute_start_script(args.start_cmd)
    yaml_data = tasks.load_app_yaml()
    client.register_unit(args.app_name, yaml_data)
    client.post_app_yaml(args.app_name, yaml_data)
    tasks.run_build_hooks(yaml_data, envs=envs)
    tasks.write_circus_conf(envs=envs)


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
