import sys
import argparse

from tsuru_unit_agent import tasks
from tsuru_unit_agent.client import Client


def run_action(args):
    client = Client(args.url, args.token)
    envs = client.register_unit(args.app_name)
    tasks.save_apprc_file(envs)
    tasks.execute_start_script(args.start_cmd, envs)
    return client, envs


def deploy_action(args):
    client, envs = run_action(args)
    yaml_data = tasks.load_app_yaml()
    client.post_app_yaml(args.app_name, yaml_data)
    tasks.run_hooks(yaml_data, envs)


actions = {
    'run': run_action,
    'deploy': deploy_action
}


def parse_args(args=None):
    if args is None:
        args = sys.argv[1:]
    parser = argparse.ArgumentParser(description='Runs tsuru-unit-agent.')
    parser.add_argument('action', choices=actions.keys(), help='Action being executed')
    parser.add_argument('url', help='URL for tsuru API server')
    parser.add_argument('token', help='Authentication token for tsuru API server')
    parser.add_argument('app_name', help='The app name')
    parser.add_argument('start_cmd', help='Command to run after notifying tsuru API server')
    return parser.parse_args(args)


def main():
    args = parse_args()
    actions[args.action](args)


if __name__ == '__main__':
    main()
