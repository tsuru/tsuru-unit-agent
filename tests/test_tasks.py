from unittest import TestCase
import mock
import os

from tsuru_unit_agent.tasks import execute_start_script, save_apprc_file, run_hooks, load_app_yaml


class TestTasks(TestCase):

    @mock.patch("subprocess.Popen")
    def test_execute(self, popen_mock):
        environs = [
            {"name": "DATABASE_HOST", "value": "localhost", "public": True},
            {"name": "DATABASE_USER", "value": "root", "public": True},
        ]
        execute_start_script("my_command", environs)
        popen_mock.assert_called_with("my_command", shell=False, cwd="/home/application/current", env={
            "DATABASE_HOST": "localhost",
            "DATABASE_USER": "root",
        })

    @mock.patch("io.open")
    def test_save_apprc_file(self, open_mock):
        file_mock = open_mock.return_value
        environs = [
            {"name": "DATABASE_HOST", "value": "localhost", "public": True},
            {"name": "DATABASE_USER", "value": "root", "public": True},
        ]

        save_apprc_file(environs)

        open_mock.assert_called_with("/home/application/apprc", "w")
        file_mock.write.assert_called()


class RunHooksTest(TestCase):
    @mock.patch("subprocess.Popen")
    def test_execute_commands(self, popen_call):
        data = {"hooks": {"build": ["ble"]}}
        envs = [
            {"name": "my_key", "value": "my_value"},
        ]
        run_hooks(data, envs)
        popen_call.assert_called_with("ble", shell=True,
                                      cwd="/home/application/current", env={'my_key': 'my_value'})

    @mock.patch("subprocess.Popen")
    def test_execute_commands_hooks_empty(self, subprocess_call):
        data = {}
        run_hooks(data, [])
        subprocess_call.assert_not_called()
        data = {"hooks": None}
        run_hooks(data, [])
        subprocess_call.assert_not_called()
        data = {"hooks": {"build": None}}
        run_hooks(data, [])
        subprocess_call.assert_not_called()
        data = {"hooks": {"build": []}}
        run_hooks(data, [])
        subprocess_call.assert_not_called()


class LoadAppYamlTest(TestCase):
    def setUp(self):
        self.working_dir = os.path.dirname(__file__)
        self.data = '''
hooks:
  build:
    - {0}_1
    - {0}_2'''

    def test_load_app_yaml(self):
        filenames = ["tsuru.yaml", "tsuru.yml", "app.yaml", "app.yml"]
        for name in filenames:
            with open(os.path.join(self.working_dir, name), "w") as f:
                f.write(self.data.format(name))

        for name in filenames:
            data = load_app_yaml(self.working_dir)
            self.assertEqual(data, {"hooks": {"build": ["{}_1".format(name), "{}_2".format(name)]}})
            os.remove(os.path.join(self.working_dir, name))

    def test_load_without_app_files(self):
        data = load_app_yaml(self.working_dir)
        self.assertEqual(data, None)
