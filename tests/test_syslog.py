# Copyright 2014 tsuru-unit-agent authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import logging
import unittest

from logging import handlers
from socket import AF_INET, SOCK_STREAM, error

import mock

from tsuru_unit_agent import syslog


class SysLogHandlerTestCase(unittest.TestCase):

    def test_inherits_from_stdlib_syslog(self):
        assert issubclass(syslog.SysLogHandler, handlers.SysLogHandler)

    @mock.patch("socket.socket")
    def test_emit_reconnects_in_case_of_failure(self, socket_mock):
        socket_mock.return_value = reconnected_socket = mock.Mock()
        handler = syslog.SysLogHandler(address=("127.0.0.1", 3030), facility="local0",
                                       socktype=SOCK_STREAM)
        handler.socket = socket = mock.Mock()
        socket.sendall.side_effect = error("something went wrong")
        record = logging.LogRecord("name", "info", "/file.py", 15, "wow", "", "")
        handler.emit(record)
        socket_mock.assert_called_with(AF_INET, SOCK_STREAM)
        reconnected_socket.connect.assert_called_with(("127.0.0.1", 3030))
        reconnected_socket.sendall.assert_called_with(mock.ANY)
