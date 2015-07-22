# Copyright 2015 tsuru-unit-agent authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import unittest
import mock
import socket
import Queue
import time

from tsuru_unit_agent.stream import Stream, TsuruLogWriter, LogEntry, QUEUE_DONE_MESSAGE

mocked_environ = {
    "TSURU_APPNAME": "appname1",
    "TSURU_HOST": "host1",
    "TSURU_APP_TOKEN": "secret123",
    "TSURU_SYSLOG_SERVER": "host2",
    "TSURU_SYSLOG_PORT": "514",
    "TSURU_SYSLOG_FACILITY": "LOCAL0",
    "TSURU_SYSLOG_SOCKET": "udp",
}


@mock.patch("os.environ", mocked_environ)
class StreamTestCase(unittest.TestCase):

    @mock.patch("os.environ", mocked_environ)
    @mock.patch("tsuru_unit_agent.stream.gethostname")
    @mock.patch("tsuru_unit_agent.stream.TsuruLogWriter")
    def setUp(self, TsuruLogWriter, gethostname):
        TsuruLogWriter.return_value = log_writer = mock.Mock()
        gethostname.return_value = "myhost"
        l_out = "2012-11-06 17:13:55 [12019] [INFO] Starting gunicorn 0.15.0\n"
        l_err = "2012-11-06 17:13:55 [12019] [ERROR] Error starting gunicorn\n"
        self.data = {}
        self.data["stderr"] = {
            "pid": 12018,
            "data": l_err,
            "name": "stderr"
        }
        self.data["stdout"] = {
            "pid": 12018,
            "data": l_out,
            "name": "stdout"
        }
        self.stream = Stream(watcher_name="mywatcher")
        TsuruLogWriter.assert_called_with(
            mock.ANY, self.stream.queue, None, None, 'host2', '514', 'LOCAL0', 'udp', 'appname1')
        log_writer.start.assert_called_once()

    def tearDown(self):
        self.stream.writer.stop()

    def test_should_have_the_close_method(self):
        self.assertTrue(hasattr(Stream, "close"))

    def test_should_send_done_message_on_close(self):
        self.stream.close()
        entry = self.stream.queue.get()
        self.assertEqual(entry, QUEUE_DONE_MESSAGE)

    def test_should_send_log_to_tsuru(self):
        self.stream(self.data["stdout"])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream._load_envs()
        url = "{0}/apps/{1}/log?source=mywatcher&unit=myhost".format(host,
                                                                     appname)
        expected_msg = "Starting gunicorn 0.15.0\n"
        entry = self.stream.queue.get()
        self.assertEqual(url, entry.url)
        self.assertEqual(2, entry.timeout)
        self.assertEqual([expected_msg], entry.messages)

    def test_should_send_log_to_syslog_as_info(self):
        self.stream(self.data["stdout"])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream._load_envs()
        expected_msg = "Starting gunicorn 0.15.0\n"
        entry = self.stream.queue.get()
        self.assertEqual(entry.messages, [expected_msg])
        self.assertEqual(entry.stream_name, "stdout")

    def test_should_send_log_to_syslog_as_error(self):
        self.stream(self.data["stderr"])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream._load_envs()
        expected_msg = "Error starting gunicorn\n"
        entry = self.stream.queue.get()
        self.assertEqual(entry.messages, [expected_msg])
        self.assertEqual(entry.stream_name, "stderr")

    @mock.patch("tsuru_unit_agent.stream.gethostname")
    @mock.patch("tsuru_unit_agent.stream.TsuruLogWriter")
    def test_timeout_is_configurable(self, TsuruLogWriter, gethostname):
        TsuruLogWriter.return_value = mock.Mock()
        gethostname.return_value = "myhost"
        stream = Stream(watcher_name="watcher", timeout=10)
        stream(self.data["stdout"])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = self.stream._load_envs()
        url = "{0}/apps/{1}/log?source=watcher&unit=myhost".format(host,
                                                                   appname)
        expected_msg = "Starting gunicorn 0.15.0\n"
        entry = stream.queue.get(timeout=2)
        self.assertEqual(url, entry.url)
        self.assertEqual(10, entry.timeout)
        self.assertEqual([expected_msg], entry.messages)

    @mock.patch("tsuru_unit_agent.stream.gethostname")
    @mock.patch("tsuru_unit_agent.stream.TsuruLogWriter")
    def test_envs_may_be_overriden(self, TsuruLogWriter, gethostname):
        TsuruLogWriter.return_value = mock.Mock()
        gethostname.return_value = "myhost"
        stream = Stream(watcher_name="watcher", envs={"TSURU_APPNAME": "mynewappname"})
        stream(self.data["stdout"])
        (appname, host, token, syslog_server,
         syslog_port, syslog_facility, syslog_socket) = stream._load_envs()
        self.assertEqual(appname, "mynewappname")
        self.assertEqual(host, "host1")
        self.assertEqual(token, "secret123")
        self.assertEqual(syslog_server, "host2")
        self.assertEqual(syslog_port, "514")
        self.assertEqual(syslog_facility, "LOCAL0")
        self.assertEqual(syslog_socket, "udp")

    @mock.patch("tsuru_unit_agent.stream.gethostname")
    @mock.patch("tsuru_unit_agent.stream.TsuruLogWriter")
    def test_envs_with_rate_limit(self, TsuruLogWriter, gethostname):
        TsuruLogWriter.return_value = mock.Mock()
        gethostname.return_value = "myhost"
        stream = Stream(watcher_name="watcher", envs={
            "LOG_RATE_LIMIT_WINDOW": "60",
            "LOG_RATE_LIMIT_COUNT": "1000",
        })
        TsuruLogWriter.assert_called_with(
            mock.ANY, stream.queue, "60", "1000", 'host2', '514', 'LOCAL0', 'udp', 'appname1')

    @mock.patch("tsuru_unit_agent.stream.TsuruLogWriter")
    @mock.patch("os.environ", {})
    def test_should_slience_errors_when_envs_does_not_exist(self, TsuruLogWriter):
        try:
            stream = Stream()
            stream(self.data["stdout"])
        except Exception as e:
            msg = "Should not fail when envs does not exist. " \
                  "Exception: {}".format(e)
            self.fail(msg)

    def test_get_messagess_no_buffering(self):
        msg = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
              "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] " \
              "[INFO] Using worker: sync\n2012-11-06 18:30:10 [13890] " \
              "[INFO] Booting worker with pid: 13890\n2012-11-06 18:30:10 " \
              "[13890] [ERROR] Exception in worker process:\nTraceback " \
              "(most recent call last):\n"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
            "Traceback (most recent call last):\n",
        ]
        messages = self.stream._get_messages(msg)
        self.assertEqual("", self.stream._buffer)
        self.assertEqual(expected, messages)

    def test_get_messagess_buffering(self):
        msg = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
              "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] " \
              "[INFO] Using worker: sync\n2012-11-06 18:30:10 [13890] " \
              "[INFO] Booting worker with pid: 13890\n2012-11-06 18:30:10 " \
              "[13890] [ERROR] Exception in worker process:\nTraceback " \
              "(most recent call last):"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
        ]
        messages = self.stream._get_messages(msg)
        self.assertEqual("Traceback (most recent call last):", self.stream._buffer)
        self.assertEqual(expected, messages)

    def test_get_messagess_buffered(self):
        msg1 = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
               "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] "
        msg2 = "[INFO] Using worker: sync\n2012-11-06 18:30:10 "
        msg3 = "[13890] [INFO] Booting worker with pid: 13890\n2012-11-06 " \
               "18:30:10 [13890] [ERROR] Exception in worker process:\n" \
               "Traceback (most recent call last):\n"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
            "Traceback (most recent call last):\n",
        ]
        self.assertEqual(expected[:1], self.stream._get_messages(msg1))
        self.assertEqual(expected[1:2], self.stream._get_messages(msg2))
        self.assertEqual(expected[2:], self.stream._get_messages(msg3))

    def test_get_messagess_full_buffer(self):
        self.stream._max_buffer_size = 20
        self.stream._buffer = 13 * "a"
        msg = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
              "http://127.0.0.1:8000 (13887)"
        expected = [self.stream._buffer +
                    "Listening at: http://127.0.0.1:8000 (13887)"]
        self.assertEqual(expected, self.stream._get_messages(msg))

    def test_get_messages_buffered_multiple_times(self):
        msg1 = "2012-11-06 18:30:10 [13887] [INFO] Listening at: " \
               "http://127.0.0.1:8000 (13887)\n2012-11-06 18:30:10 [13887] "
        msg2 = "[INFO] Using worker: sync\n2012-11-06 18:30:10 "
        msg3 = "[13890] [INFO] Booting worker with pid: 13890\n2012-11-06 " \
               "18:30:10 [13890] [ERROR] Exception in worker process:\n" \
               "Traceback (most recent call last):"
        msg4 = "\n2012-11-06 18:30:10 [13887] [INFO] Booting another worker "\
               "with pid: 13891\n"
        expected = [
            "Listening at: http://127.0.0.1:8000 (13887)\n",
            "Using worker: sync\n",
            "Booting worker with pid: 13890\n",
            "Exception in worker process:\n",
            "Traceback (most recent call last):\n",
            "Booting another worker with pid: 13891\n",
        ]
        self.assertEqual(expected[:1], self.stream._get_messages(msg1))
        self.assertEqual(expected[1:2], self.stream._get_messages(msg2))
        self.assertEqual(expected[2:4], self.stream._get_messages(msg3))
        self.assertEqual(expected[4:], self.stream._get_messages(msg4))

    def test_get_messages_sequential_bufferings(self):
        msg1 = "2012-11-06 18:30:10 [13887] [INFO] Listening at: "
        msg2 = "http://127.0.0.1:8000 "
        msg3 = "(13887)\n"
        self.assertEqual([], self.stream._get_messages(msg1))
        self.assertEqual([], self.stream._get_messages(msg2))
        self.assertEqual(["Listening at: http://127.0.0.1:8000 (13887)\n"],
                         self.stream._get_messages(msg3))

    def test_default_max_buffer_size(self):
        self.assertEqual(10240, self.stream._max_buffer_size)

    @mock.patch("tsuru_unit_agent.stream.TsuruLogWriter")
    def test_max_buffer_size_is_configurable(self, TsuruLogWriter):
        stream = Stream(max_buffer_size=500)
        self.assertEqual(500, stream._max_buffer_size)


class TsuruLogWriterTestCase(unittest.TestCase):

    def test_rate_limit(self):
        session = mock.Mock()
        queue = Queue.Queue(maxsize=1000)
        writer = TsuruLogWriter(session, queue, 2, 10, None, None, None, None, None)
        writer.start()
        for i in xrange(20):
            queue.put_nowait(LogEntry('url', 1, ['msg1'], None))
        while not queue.empty():
            time.sleep(0.01)
        self.assertEqual(session.post.call_count, 11)
        session.post.assert_any_call('url', data='["msg1"]', timeout=1)
        session.post.assert_any_call(
            'url',
            data='["dropping messages, more than 10 messages in last 2 seconds"]', timeout=1
        )
        time.sleep(3)
        for i in xrange(20):
            queue.put_nowait(LogEntry('url', 1, ['msg2'], None))
        queue.put_nowait(QUEUE_DONE_MESSAGE)
        writer.join()
        self.assertEqual(session.post.call_count, 22)
        session.post.assert_any_call('url', data='["msg2"]', timeout=1)

    def test_rate_limit_stress(self):
        session = mock.Mock()
        queue = Queue.Queue(maxsize=1000)
        writer = TsuruLogWriter(session, queue, "2", "10", None, None, None, None, None)
        writer.start()
        t0 = time.time()
        i = 0
        while time.time() - t0 < 10:
            i += 1
            try:
                queue.put_nowait(LogEntry('url', 1, ['msg-{}'.format(i)], None))
            except:
                pass
        while queue.full():
            time.sleep(0.1)
        queue.put_nowait(QUEUE_DONE_MESSAGE)
        writer.join()
        self.assertTrue(45 < session.post.call_count <= 66)
        session.post.assert_any_call('url', data='["msg-1"]', timeout=1)

    def test_rate_limit_not_configured(self):
        session = mock.Mock()
        queue = Queue.Queue(maxsize=1000)
        writer = TsuruLogWriter(session, queue, None, None, None, None, None, None, None)
        writer.start()
        for i in xrange(100):
            queue.put_nowait(LogEntry('url', 1, ['msg-1'], None))
        queue.put_nowait(QUEUE_DONE_MESSAGE)
        writer.join()
        self.assertEqual(session.post.call_count, 100)
        session.post.assert_called_with('url', data='["msg-1"]', timeout=1)

    def test_rate_limit_invalid_config(self):
        session = mock.Mock()
        queue = Queue.Queue(maxsize=1000)
        writer = TsuruLogWriter(session, queue, "", {}, None, None, None, None, None)
        writer.start()
        for i in xrange(100):
            queue.put_nowait(LogEntry('url', 1, ['msg-1'], None))
        queue.put_nowait(QUEUE_DONE_MESSAGE)
        writer.join()
        self.assertEqual(session.post.call_count, 100)
        session.post.assert_any_call('url', data='["msg-1"]', timeout=1)

    @mock.patch("logging.getLogger")
    @mock.patch("tsuru_unit_agent.syslog.SysLogHandler")
    def test_send_log_to_syslog_as_info(self, s_handler, logger):
        s_handler.return_value = syslog = mock.Mock()
        session = mock.Mock()
        queue = Queue.Queue(maxsize=1000)
        writer = TsuruLogWriter(session, queue, "", {}, 'host2', '514', 'LOCAL0', 'udp', 'appname1')
        writer.start()
        for i in xrange(10):
            queue.put_nowait(LogEntry('url', 1, ['msg-1'], 'stdout'))
        queue.put_nowait(QUEUE_DONE_MESSAGE)
        writer.join()
        self.assertEqual(session.post.call_count, 10)
        session.post.assert_any_call('url', data='["msg-1"]', timeout=1)
        logger.assert_called_with('appname1')
        my_logger = logger.return_value
        s_handler.assert_called_with(address=('host2', 514),
                                     facility='LOCAL0',
                                     socktype=socket.SOCK_DGRAM)
        my_logger.addHandler.assert_called_with(syslog)
        my_logger.info.assert_called_with("msg-1")

    @mock.patch("logging.getLogger")
    @mock.patch("tsuru_unit_agent.syslog.SysLogHandler")
    def test_send_log_to_syslog_as_error(self, s_handler, logger):
        s_handler.return_value = syslog = mock.Mock()
        session = mock.Mock()
        queue = Queue.Queue(maxsize=1000)
        writer = TsuruLogWriter(session, queue, "", {}, 'host2', '514', 'LOCAL0', 'udp', 'appname1')
        writer.start()
        for i in xrange(10):
            queue.put_nowait(LogEntry('url', 1, ['msg-1'], 'stderr'))
        queue.put_nowait(QUEUE_DONE_MESSAGE)
        writer.join()
        self.assertEqual(session.post.call_count, 10)
        session.post.assert_any_call('url', data='["msg-1"]', timeout=1)
        logger.assert_called_with('appname1')
        my_logger = logger.return_value
        s_handler.assert_called_with(address=('host2', 514),
                                     facility='LOCAL0',
                                     socktype=socket.SOCK_DGRAM)
        my_logger.addHandler.assert_called_with(syslog)
        my_logger.error.assert_called_with("msg-1")
