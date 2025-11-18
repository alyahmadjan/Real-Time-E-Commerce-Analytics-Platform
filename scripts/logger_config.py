"""
Updated logger_config.py

Configuration module for logging with timestamped rotating file handler.
This module should be placed in the scripts folder.
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Get project directory paths
SCRIPT_DIR = Path(__file__).parent  # scripts folder
PROJECT_DIR = SCRIPT_DIR.parent  # Real-Time-E-Commerce-Analytics-Platform
LOGS_DIR = PROJECT_DIR / "logs"


class TimestampRotatingFileHandler(RotatingFileHandler):
    """
    A custom handler that creates a new log file with a timestamp when rotation occurs.
    """

    def doRollover(self):
        """Override the doRollover method to create a new file with a timestamp."""
        if self.stream:
            self.stream.close()
            self.stream = None

        # Generate a timestamp for the new log file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.baseFilename = os.path.join(
            os.path.dirname(self.baseFilename),
            f'shopify_sync_{timestamp}.log'
        )
        self.mode = 'w'
        self.stream = self._open()


def setup_logger():
    """Configure and return a logger with timestamped rotating file handler"""
    # Ensure the logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)

    # Generate a timestamp for the initial log file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(LOGS_DIR, f'shopify_sync_{timestamp}.log')

    # Create a logger
    logger_instance = logging.getLogger('update_shopify_history_database_logger')
    logger_instance.setLevel(logging.DEBUG)  # Set to DEBUG to capture all levels

    # Remove existing handlers to avoid duplicates
    for handler in logger_instance.handlers[:]:
        logger_instance.removeHandler(handler)

    # Create a custom rotating file handler with UTF-8 encoding
    file_handler = TimestampRotatingFileHandler(
        filename=log_file,
        maxBytes=1024 * 1024,  # 1 MB
        backupCount=0,  # No backup files, as we're creating new files with timestamps
        encoding='utf-8'  # Ensure UTF-8 encoding
    )

    # Also add console handler for real-time output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Define the log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger_instance.addHandler(file_handler)
    logger_instance.addHandler(console_handler)

    return logger_instance


# Create and export logger instance
logger = setup_logger()
