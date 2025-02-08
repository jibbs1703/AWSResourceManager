"""Logger Module for AWS Resource Manager"""
import logging

def configure_logger():
    # Create a logger
    logger = logging.getLogger(__name__)  # Or a specific name
    logger.setLevel(logging.DEBUG)  # Set the minimum level to log

    # Create a handler for console output (stderr by default)
    handler = logging.StreamHandler()

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger

if __name__ == '__main__':
    # Create Console Logger from Function
    logger = configure_logger()
    # Print Dummy Messages
    logger.debug('This is a debug message.')
    logger.info('This is an info message.')
    logger.warning('This is a warning message.')
    logger.error('This is an error message.')
    logger.critical('This is a critical message.')