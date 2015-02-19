import unittest
import mock

from requests.exceptions import ConnectionError
from tsuru_unit_agent.main import parse_args, main


class TestMain(unittest.TestCase):
    def test_parse_args(self):
        args = parse_args(['a', 'b', 'c', 'd', 'run'])
        self.assertEqual(args.action, 'run')
        self.assertEqual(args.url, 'a')
        self.assertEqual(args.token, 'b')
        self.assertEqual(args.app_name, 'c')
        self.assertEqual(args.start_cmd, 'd')

    def test_parse_args_default_action(self):
        args = parse_args(['a', 'b', 'c', 'd'])
        self.assertEqual(args.action, 'run')
        self.assertEqual(args.url, 'a')
        self.assertEqual(args.token, 'b')
        self.assertEqual(args.app_name, 'c')
        self.assertEqual(args.start_cmd, 'd')

    def test_parse_args_deploy(self):
        args = parse_args(['a', 'b', 'c', 'd', 'deploy'])
        self.assertEqual(args.action, 'deploy')
        self.assertEqual(args.url, 'a')
        self.assertEqual(args.token, 'b')
        self.assertEqual(args.app_name, 'c')
        self.assertEqual(args.start_cmd, 'd')

    def test_parse_args_invalid(self):
        self.assertRaises(SystemExit, parse_args, [])
        self.assertRaises(SystemExit, parse_args, ['a', 'b', 'c', 'd', 'e'])

    @mock.patch('sys.argv', ['', 'http://localhost', 'token', 'app1', 'mycmd', 'deploy'])
    @mock.patch('tsuru_unit_agent.main.tasks')
    @mock.patch('tsuru_unit_agent.main.Client')
    def test_main_deploy_action(self, client_mock, tasks_mock):
        register_mock = client_mock.return_value.register_unit
        register_mock.return_value = {'env1': 'val1'}
        exec_script_mock = tasks_mock.execute_start_script
        load_yaml_mock = tasks_mock.load_app_yaml
        load_yaml_mock.return_value = {'hooks': {'build': ['cmd_1', 'cmd_2']}}
        post_app_yaml_mock = client_mock.return_value.post_app_yaml
        run_build_hooks_mock = tasks_mock.run_build_hooks
        write_circus_conf_mock = tasks_mock.write_circus_conf
        save_apprc_mock = tasks_mock.save_apprc_file
        main()
        call_count = len(client_mock.mock_calls) + len(tasks_mock.mock_calls)
        self.assertEqual(call_count, 9)
        client_mock.assert_called_once_with('http://localhost', 'token')
        register_mock.assert_any_call('app1')
        register_mock.assert_any_call('app1', load_yaml_mock.return_value)
        save_apprc_mock.assert_called_once_with(register_mock.return_value)
        exec_script_mock.assert_called_once_with('mycmd')
        load_yaml_mock.assert_called_once_with()
        write_circus_conf_mock.assert_called_once_with(envs={'env1': 'val1'})
        post_app_yaml_mock.assert_called_once_with('app1', load_yaml_mock.return_value)
        run_build_hooks_mock.assert_called_once_with(load_yaml_mock.return_value,
                                                     envs={'env1': 'val1'})

    @mock.patch('sys.argv', ['', 'http://localhost', 'token', 'app1', 'mycmd', 'run'])
    @mock.patch('tsuru_unit_agent.main.tasks')
    @mock.patch('tsuru_unit_agent.main.Client')
    def test_main_run_action(self, client_mock, tasks_mock):
        register_mock = client_mock.return_value.register_unit
        register_mock.return_value = {'env1': 'val1'}
        save_apprc_mock = tasks_mock.save_apprc_file
        exec_script_mock = tasks_mock.execute_start_script
        run_restart_hooks_mock = tasks_mock.run_restart_hooks
        write_circus_conf_mock = tasks_mock.write_circus_conf
        load_yaml_mock = tasks_mock.load_app_yaml
        load_yaml_mock.return_value = {'hooks': {'build': ['cmd_1', 'cmd_2']}}
        main()
        call_count = len(client_mock.mock_calls) + len(tasks_mock.mock_calls)
        self.assertEqual(call_count, 8)
        write_circus_conf_mock.assert_called_once_with(envs={'env1': 'val1'})
        client_mock.assert_called_once_with('http://localhost', 'token')
        register_mock.assert_called_once_with('app1')
        save_apprc_mock.assert_called_once_with(register_mock.return_value)
        exec_script_mock.assert_called_once_with('mycmd', envs={'env1': 'val1'}, with_shell=False)
        load_yaml_mock.assert_called_once_with()
        run_restart_hooks_mock.assert_any_call('before', load_yaml_mock.return_value,
                                               envs={'env1': 'val1'})
        run_restart_hooks_mock.assert_any_call('after', load_yaml_mock.return_value,
                                               envs={'env1': 'val1'})

    @mock.patch('sys.argv', ['', 'http://localhost', 'token', 'app1', 'mycmd', 'run'])
    @mock.patch('tsuru_unit_agent.main.tasks')
    @mock.patch('tsuru_unit_agent.main.Client')
    def test_main_run_action_api_error(self, client_mock, tasks_mock):
        register_mock = client_mock.return_value.register_unit

        def fail(*args):
            raise ConnectionError()
        register_mock.side_effect = fail
        save_apprc_mock = tasks_mock.save_apprc_file
        parse_apprc_mock = tasks_mock.parse_apprc_file
        parse_apprc_mock.return_value = {'env1': 'val1'}
        exec_script_mock = tasks_mock.execute_start_script
        run_restart_hooks_mock = tasks_mock.run_restart_hooks
        write_circus_conf_mock = tasks_mock.write_circus_conf
        load_yaml_mock = tasks_mock.load_app_yaml
        load_yaml_mock.return_value = {'hooks': {'build': ['cmd_1', 'cmd_2']}}
        main()
        call_count = len(client_mock.mock_calls) + len(tasks_mock.mock_calls)
        self.assertEqual(call_count, 8)
        write_circus_conf_mock.assert_called_once_with(envs={'env1': 'val1'})
        client_mock.assert_called_once_with('http://localhost', 'token')
        register_mock.assert_called_once_with('app1')
        parse_apprc_mock.assert_called_once_with()
        self.assertEqual(save_apprc_mock.call_count, 0)
        exec_script_mock.assert_called_once_with('mycmd', envs={'env1': 'val1'}, with_shell=False)
        load_yaml_mock.assert_called_once_with()
        run_restart_hooks_mock.assert_any_call('before', load_yaml_mock.return_value,
                                               envs={'env1': 'val1'})
        run_restart_hooks_mock.assert_any_call('after', load_yaml_mock.return_value,
                                               envs={'env1': 'val1'})
