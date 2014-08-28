import unittest

from tsuru_unit_agent.main import parse_args


class TestMain(unittest.TestCase):
    def test_parse_args(self):
        args = parse_args(['run', 'a', 'b', 'c', 'd'])
        self.assertEqual(args.action, 'run')
        self.assertEqual(args.url, 'a')
        self.assertEqual(args.token, 'b')
        self.assertEqual(args.app_name, 'c')
        self.assertEqual(args.start_cmd, 'd')

    def test_parse_args_deploy(self):
        args = parse_args(['deploy', 'a', 'b', 'c', 'd'])
        self.assertEqual(args.action, 'deploy')
        self.assertEqual(args.url, 'a')
        self.assertEqual(args.token, 'b')
        self.assertEqual(args.app_name, 'c')
        self.assertEqual(args.start_cmd, 'd')

    def test_parse_args_invalid(self):
        self.assertRaises(SystemExit, parse_args, [])
        self.assertRaises(SystemExit, parse_args, ['a', 'b', 'c', 'd', 'e'])
        self.assertRaises(SystemExit, parse_args, ['run', 'a', 'b', 'c'])
