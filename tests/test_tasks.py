from tsuru_unit_agent.tasks import execute_start_script

import unittest
import mock


class TestTasks(unittest.TestCase):

    @mock.patch("subprocess.call")
    def test_execute(self, call_mock):
        execute_start_script()
        call_mock.assert_called_with(["/var/lib/tsuru/start"])
