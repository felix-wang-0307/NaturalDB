from .lock import lock_manager
from datetime import datetime

class bcolors:
    """Colors for terminal output."""
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'

class LoggerLevels:
    """Logging levels."""
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    DEBUG = 'DEBUG'
    CRITICAL = 'CRITICAL'
    SUCCESS = 'SUCCESS'


class Logger:
    """
    A simple logger class to log messages of different errors, warnings, and info.
    """

    def __init__(self, log_file='naturaldb.log', to_console=False):
        self.log_file = log_file
        self.lock = lock_manager.get_lock(log_file)
        self.to_console = to_console

    def _write_log(self, level: str, message: str) -> None:
        filename = self.log_file
        time = datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")
        self.lock.acquire_write()
        try:
            with open(filename, 'a') as f:
                f.write(f'[{time}] [{level}] {message}\n')
        finally:
            self.lock.release_write()
    
    def _console_log(self, level: str, message: str) -> None:
        color = {
            LoggerLevels.INFO: bcolors.OKBLUE,
            LoggerLevels.WARNING: bcolors.WARNING,
            LoggerLevels.ERROR: bcolors.FAIL,
            LoggerLevels.DEBUG: bcolors.OKGREEN,
            LoggerLevels.CRITICAL: bcolors.FAIL,
            LoggerLevels.SUCCESS: bcolors.OKGREEN
        }.get(level, bcolors.OKBLUE)
        print(f"{color}[{level}] {message}\033[0m")

    def log(self, level: str, message: str) -> None:
        """
        Log a message with a given level.
        """
        self._write_log(level, message)
        if self.to_console:
            self._console_log(level, message)