from tsuru_unit_agent.tasks import execute_start_script, save_apprc_file

import unittest
import mock


class TestTasks(unittest.TestCase):

    @mock.patch("subprocess.call")
    def test_execute(self, call_mock):
        execute_start_script()
        call_mock.assert_called_with(["/var/lib/tsuru/start"])

    @mock.patch("io.open")
    def test_save_apprc_file(self, open_mock):
        file_mock = open_mock.return_value
        environs = {
            "DATABASE_HOST": "localhost",
            "DATABASE_USER": "root",
        }

        save_apprc_file(environs)

        open_mock.assert_called_with("/home/application/apprc")
        file_mock.write.assert_called()
