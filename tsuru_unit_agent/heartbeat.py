import sys
import threading
import time


class StderrHeartbeat(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(StderrHeartbeat, self).__init__(*args, **kwargs)
        self.daemon = True

    def run(self):
        while True:
            sys.stderr.write("\0")
            sys.stderr.flush()
            time.sleep(5)
