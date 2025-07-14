import os
import logging
from datetime import datetime
import pytz


class KSTFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        # record.created는 UNIX timestamp
        dt = datetime.fromtimestamp(record.created, pytz.timezone("Asia/Seoul"))
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def get_logger(log_id=None):
    os.makedirs("logs", exist_ok=True)
    today = datetime.now(pytz.timezone("Asia/Seoul")).date()

    logger = logging.getLogger(log_id)
    logger.setLevel(logging.INFO)

    formatter = KSTFormatter(f"%(asctime)s - {log_id} - %(levelname)s - %(message)s")

    server_handler = logging.StreamHandler()
    server_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(f"./logs/{today}.txt")
    file_handler.setFormatter(formatter)

    logger.addHandler(server_handler)
    logger.addHandler(file_handler)

    return logger