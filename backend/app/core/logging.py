import logging
import sys

def setup_logger():
    logger = logging.getLogger("gbdoc_rag")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_logger()

def log_event(stage: str, message: str):
    """Structured event logging matching Section 34 of the master prompt."""
    logger.info(f"[{stage.upper()}] {message}")
