import logging
from logging.handlers import RotatingFileHandler
import os

# Define the log directory (will be in the data directory)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
LOG_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_FILE = os.path.join(LOG_DIR, "app_log.log")

# Create the log directory if it doesn't exist
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def setup_logger():
    """
    Sets up a centralized logger for the application.
    - Logs to a file in the 'logs' directory.
    - Rotates the log file when it reaches 2MB, keeping up to 5 backups.
    """
    # Get the root logger
    logger = logging.getLogger("USBGuardApp")
    
    # Avoid adding multiple handlers if the logger is already configured
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO) # Set the minimum level of messages to be logged

    # Create a formatter to define the log message format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create a file handler that rotates logs
    # Rotates when the log reaches 2 MB, keeps 5 backup files
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=2*1024*1024, # 2 Megabytes
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    # Optional: Add a console handler for debugging during development
    # You can comment this out for production
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info("Logger setup complete.")

    return logger

# Create the logger instance to be imported by other modules
log = setup_logger()