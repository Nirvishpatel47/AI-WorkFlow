import sys
import logging
from logging.handlers import RotatingFileHandler

class AdvancedLogger:
    def __init__(self, name="AppLogger", log_file="app.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
            )

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            file_handler = RotatingFileHandler(
                log_file, maxBytes=5*1024*1024, backupCount=5
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def info(self, message: str):
        """Standard informational logging."""
        self.logger.info(message)

    def error(self, function_name: str, error: Exception):
        """
        Safe logging for errors. 
        Captures the function name and the full traceback for debugging.
        """
        error_msg = f"Error in {function_name}: {str(error)}"
        self.logger.error(error_msg, exc_info=True)

    def warning(self, message: str):
        """Log unexpected events that aren't necessarily breaking the app."""
        self.logger.warning(message)

    def critical(self, message: str):
        """Log failures that require immediate attention."""
        self.logger.critical(f"FATAL: {message}")