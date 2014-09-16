import unittest
import mock

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
        register_mock.return_value = [{'name': 'env1', 'value': 'val1'}]
        save_apprc_mock = tasks_mock.save_apprc_file
        exec_script_mock = tasks_mock.execute_start_script
        load_yaml_mock = tasks_mock.load_app_yaml
        load_yaml_mock.return_value = {'hooks': {'build': ['cmd_1', 'cmd_2']}}
        post_app_yaml_mock = client_mock.return_value.post_app_yaml
        run_hooks_mock = tasks_mock.run_hooks
        main()
        call_count = len(client_mock.mock_calls) + len(tasks_mock.mock_calls)
        self.assertEqual(call_count, 7)
        client_mock.assert_called_once_with('http://localhost', 'token')
        register_mock.assert_called_once_with('app1')
        save_apprc_mock.assert_called_once_with(register_mock.return_value)
        exec_script_mock.assert_called_once_with('mycmd', register_mock.return_value)
        load_yaml_mock.assert_called_once()
        post_app_yaml_mock.assert_called_once_with('app1', load_yaml_mock.return_value)
        run_hooks_mock.assert_called_once_with(load_yaml_mock.return_value, register_mock.return_value)

    @mock.patch('sys.argv', ['', 'http://localhost', 'token', 'app1', 'mycmd', 'run'])
    @mock.patch('tsuru_unit_agent.main.tasks')
    @mock.patch('tsuru_unit_agent.main.Client')
    def test_main_run_action(self, client_mock, tasks_mock):
        register_mock = client_mock.return_value.register_unit
        register_mock.return_value = [{'name': 'env1', 'value': 'val1'}]
        save_apprc_mock = tasks_mock.save_apprc_file
        exec_script_mock = tasks_mock.execute_start_script
        main()
        call_count = len(client_mock.mock_calls) + len(tasks_mock.mock_calls)
        self.assertEqual(call_count, 4)
        client_mock.assert_called_once_with('http://localhost', 'token')
        register_mock.assert_called_once_with('app1')
        save_apprc_mock.assert_called_once_with(register_mock.return_value)
        exec_script_mock.assert_called_once_with('mycmd', register_mock.return_value)
