import logging

def get_logger(name: str, level=logging.INFO):
    """
    Returns a configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If handlers are already present, don't add them again
    if not logger.handlers:
        # Create a console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)

        # Create a formatter and set it for the handler
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(ch)

    return logger

