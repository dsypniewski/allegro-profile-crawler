from datetime import datetime


class Logger(object):
    _log_file = None
    _error_log_file = None

    @staticmethod
    def init(mode='a', log_filename='log.txt', error_log_filename='error_log.txt'):
        Logger._log_file = open(log_filename, mode, encoding='utf-8')
        Logger._error_log_file = open(error_log_filename, mode, encoding='utf-8')

    @staticmethod
    def _timestamp():
        return '[' + str(datetime.now()) + '] '

    @staticmethod
    def message(msg):
        if Logger._log_file is None:
            raise Exception('Logger class was not initialized.')
        msg = Logger._timestamp() + msg
        print(msg)
        Logger._log_file.write(msg + '\n')
        Logger._log_file.flush()

    @staticmethod
    def error(err):
        if Logger._error_log_file is None:
            raise Exception('Logger class was not initialized.')
        err = Logger._timestamp() + err
        print(err)
        Logger._error_log_file.write(err + '\n')
        Logger._error_log_file.flush()
