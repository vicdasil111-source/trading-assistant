"""Journalisation simple et réutilisable."""

import logging

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def get_logger(name: str = "trading-assistant", level: int = logging.INFO) -> logging.Logger:
    """Renvoie un logger configuré. Idempotent : pas de doublon de handlers."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%H:%M:%S"))
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
