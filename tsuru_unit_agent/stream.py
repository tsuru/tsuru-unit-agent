# Copyright 2015 tsuru-unit-agent authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import json
import logging
import Queue
import re
import socket
import os
import threading
import time
import collections

from socket import gethostname

import requests

from . import syslog

QUEUE_DONE_MESSAGE = object()


def extract_message(msg):
    # 2012-11-06 18:30:10 [13887] [INFO]
    regex = "\d+\-\d+\-\d+ \d+\:\d+\:\d+ \[\d+\] \[\w+\] "
    msgs = re.split(regex, msg)
    return [m for m in msgs if m]


class Stream(object):

    def __init__(self, **kwargs):
        self._buffer = ""
        self._max_buffer_size = kwargs.get("max_buffer_size", 10240)
        self.watcher_name = kwargs.get("watcher_name", "")
        self.timeout = kwargs.get("timeout", 2)
        self.echo = kwargs.get("echo_output")
        self.default_stream_name = kwargs.get("default_stream_name", "stdout")
        envs = kwargs.get("envs") or {}
        self.envs = {}
        self.envs.update(os.environ)
        self.envs.update(envs)
        self.hostname = gethostname()
        self.start_writer()

    def start_writer(self):
        (appname, _, token, syslog_server, syslog_port,
         syslog_facility, syslog_socket) = self._load_envs()
        session = requests.Session()
        if token:
            session.headers.update({"Authorization": "bearer " + token})
        maxsize = int(self.envs.get("LOG_MAX_QUEUE_SIZE", 1000))
        self.queue = Queue.Queue(maxsize=maxsize)
        rate_limit_window = self.envs.get("LOG_RATE_LIMIT_WINDOW")
        rate_limit_count = self.envs.get("LOG_RATE_LIMIT_COUNT")
        self.writer = TsuruLogWriter(session, self.queue, rate_limit_window, rate_limit_count,
                                     syslog_server, syslog_port, syslog_facility, syslog_socket,
                                     appname)
        self.writer.start()

    def write(self, message):
        self({'data': message})
        if self.echo:
            self.echo.write(message)

    def flush(self):
        self._flush()
        if self.echo:
            self.echo.flush()

    def close(self):
        self.queue.put_nowait(QUEUE_DONE_MESSAGE)

    def __call__(self, data):
        (appname, host, token, _, _, _, _) = self._load_envs()
        messages = self._get_messages(data["data"])
        stream_name = data.get('name', self.default_stream_name)
        url = None
        if appname and host and token:
            url = "{0}/apps/{1}/log?source={2}&unit={3}".format(
                host, appname, self.watcher_name, self.hostname)
        try:
            self.queue.put_nowait(LogEntry(url, self.timeout, messages, stream_name))
        except:
            logging.exception("ignored error trying to add log message to queue")

    def _load_envs(self):
        return (self.envs.get("TSURU_APPNAME"), self.envs.get("TSURU_HOST"),
                self.envs.get("TSURU_APP_TOKEN"), self.envs.get("TSURU_SYSLOG_SERVER"),
                self.envs.get("TSURU_SYSLOG_PORT"),
                self.envs.get("TSURU_SYSLOG_FACILITY"),
                self.envs.get("TSURU_SYSLOG_SOCKET"))

    def _flush(self):
        if len(self._buffer) > 0:
            self._buffer += "\n"
        self.write("")

    def _get_messages(self, msg):
        result = []
        if self._buffer != "":
            msg = self._buffer + msg
            self._buffer = ""
        msgs = extract_message(msg)
        lines = "".join(msgs).splitlines(True)
        for line in lines:
            if (line.endswith("\n") or len(line) > self._max_buffer_size):
                result.append(line)
            else:
                self._buffer = line
        return result


RATE_LIMITED = '["dropping messages, more than {} messages in last {} seconds"]'


class TsuruLogWriter(threading.Thread):

    def __init__(self, session, queue, rate_limit_window, rate_limit_count,
                 syslog_server, syslog_port, syslog_facility, syslog_socket,
                 appname, *args, **kwargs):
        super(TsuruLogWriter, self).__init__(*args, **kwargs)
        self.queue = queue
        self.session = session
        self.syslog_server = syslog_server
        self.syslog_port = syslog_port
        self.syslog_facility = syslog_facility
        self.syslog_socket = syslog_socket
        self.appname = appname
        self.hostname = gethostname()
        self.setup_rate_limiter(rate_limit_window, rate_limit_count)

    def setup_rate_limiter(self, rate_limit_window, rate_limit_count):
        self.rate_limit_enabled = rate_limit_window is not None and rate_limit_count is not None
        if not self.rate_limit_enabled:
            return
        try:
            self.rate_limit_window = int(rate_limit_window)
            self.rate_limit_count = int(rate_limit_count)
        except:
            logging.exception(
                "Invalid values for rate limiting env vars, window: '{}' count: '{}'"
                .format(rate_limit_window, rate_limit_count)
            )
            self.rate_limit_enabled = False
            return
        self.rate_limit_notice = 0
        self.rate_queue = collections.deque()

    def should_accept_log(self):
        if not self.rate_limit_enabled:
            return True
        now = time.time()
        max_time = now - self.rate_limit_window
        while len(self.rate_queue) > 0 and self.rate_queue[0] < max_time:
            self.rate_queue.popleft()
        if len(self.rate_queue) >= self.rate_limit_count:
            return False
        self.rate_queue.append(now)
        return True

    def _get_syslog(self):
        if not hasattr(self, "_syslog"):
            if self.syslog_socket == 'tcp':
                socket_type = socket.SOCK_STREAM
            else:
                socket_type = socket.SOCK_DGRAM
            self._syslog = syslog.SysLogHandler(address=(self.syslog_server, int(self.syslog_port)),
                                                facility=self.syslog_facility,
                                                socktype=socket_type)
            formatter = logging.Formatter('%(asctime)s {0} %(name)s: %(message)s'.format(self.hostname),
                                          "%b %d %H:%M:%S")
            self._syslog.setFormatter(formatter)
        return self._syslog

    def _log_syslog(self, messages, stream_name):
        try:
            syslog = self._get_syslog()
            logger = logging.getLogger(self.appname)
            logger.handlers = []
            logger.setLevel(logging.INFO)
            logger.addHandler(syslog)
            for m in messages:
                if stream_name == 'stdout':
                    logger.info(m)
                else:
                    logger.error(m)
        except:
            pass

    def run(self):
        while True:
            try:
                entry = self.queue.get()
                if entry == QUEUE_DONE_MESSAGE:
                    break
                if self.syslog_server and self.syslog_port and self.syslog_facility:
                    self._log_syslog(entry.messages, entry.stream_name)
                if not entry.url:
                    continue
                if not self.should_accept_log():
                    now = time.time()
                    if self.rate_limit_notice < now - self.rate_limit_window:
                        msg = RATE_LIMITED.format(self.rate_limit_count, self.rate_limit_window)
                        self.session.post(
                            entry.url,
                            data=msg,
                            timeout=entry.timeout)
                        self.rate_limit_notice = now
                    continue
                try:
                    self.session.post(entry.url, data=json.dumps(entry.messages),
                                      timeout=entry.timeout)
                finally:
                    self.queue.task_done()
            except:
                pass


class LogEntry(object):

    def __init__(self, url, timeout, messages, stream_name):
        self.url = url
        self.timeout = timeout
        self.messages = messages
        self.stream_name = stream_name
