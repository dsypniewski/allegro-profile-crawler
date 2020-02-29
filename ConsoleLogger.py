import sys


class ConsoleLogger(object):
    _terminal = None
    _log_file = None

    def __init__(self, filename, mode='a'):
        self._terminal = sys.stdout
        self._log_file = open(filename, mode, encoding='utf-8')

    def write(self, message):
        self._terminal.write(message)
        self._log_file.write(str(message))
        self._log_file.flush()

    def flush(self):
        self._log_file.flush()

    @staticmethod
    def init(mode='a', stdout_filename='console.txt', stderr_filename='stderr.txt'):
        sys.stdout = ConsoleLogger(stdout_filename, mode)
        sys.stderr = ConsoleLogger(stderr_filename, mode)
