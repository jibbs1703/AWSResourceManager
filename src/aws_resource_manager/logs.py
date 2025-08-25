"""Logger Module for AWS Resource Manager"""

import logging


def get_logger():
    configured_logger = logging.getLogger(__name__)
    configured_logger.setLevel(logging.DEBUG) 

    handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    configured_logger.addHandler(handler)

    return configured_logger


if __name__ == "__main__":
    logger = get_logger()
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")
