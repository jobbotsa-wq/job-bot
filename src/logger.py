import logging
import os
from datetime import datetime


def setup_logger(user_id: str = "general") -> logging.Logger:
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(logs_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(logs_dir, f"{timestamp}_{user_id}.txt")

    logger = logging.getLogger(f"jobbot.{user_id}")
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        logger.handlers.clear()

    # Archivo — todos los niveles con detalle completo
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(module)-20s | %(funcName)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    # Consola — solo INFO y superiores
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S"
    ))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logger iniciado — archivo: {log_file}")
    return logger
