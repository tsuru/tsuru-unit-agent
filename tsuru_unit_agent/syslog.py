# Copyright 2014 tsuru-unit-agent authors. All rights reserved.
# Use of this source code is governed by a BSD-style
# license that can be found in the LICENSE file.

import socket

from logging import handlers


class SysLogHandler(handlers.SysLogHandler):

    def emit(self, record, retry=True):
        msg = self.format(record) + '\000'
        prio = '<%d>' % self.encodePriority(self.facility,
                                            self.mapPriority(record.levelname))
        if type(msg) is unicode:
            msg = msg.encode('utf-8')
        msg = prio + msg
        try:
            if self.unixsocket:
                try:
                    self.socket.send(msg)
                except socket.error:
                    self.socket.close()
                    self._connect_unixsocket(self.address)
                    self.socket.send(msg)
            elif self.socktype == socket.SOCK_DGRAM:
                self.socket.sendto(msg, self.address)
            else:
                try:
                    self.socket.sendall(msg)
                except socket.error:
                    if retry:
                        self.socket = socket.socket(socket.AF_INET, self.socktype)
                        self.socket.connect(self.address)
                        self.emit(record, retry=False)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
