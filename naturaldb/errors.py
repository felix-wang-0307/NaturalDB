from .logger import Logger
class NaturalDBError(Exception):
    """Base class for all exceptions raised by NaturalDB."""
    def __init__(self, message: str, type: str = "NaturalDBError"):
        super().__init__(message)
        self.type = type
        self.logger = Logger(log_file="naturaldb_errors.log", to_console=True)
        self._log()

    def _log(self):
        self.logger.log("ERROR", f"{self.type}: {self.args[0]}")
    
