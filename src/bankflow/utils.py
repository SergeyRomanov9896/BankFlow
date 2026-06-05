import logging
import os

import pandas as pd

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("transactions")
file_h = logging.FileHandler("logs/transactions.log", mode="w", encoding="utf-8")
fmt = logging.Formatter("%(asctime)s | %(filename)s | %(levelname)s | %(message)s")

file_h.setFormatter(fmt)
logger.addHandler(file_h)
logger.setLevel(logging.DEBUG)


def load_transactions_from_excel(path: str = "data/operations.xlsx"):
    try:
        df = pd.read_excel(path)
        return df.to_dict(orient="records")
    except FileNotFoundError:
        logger.error("Файл не найден: %s", path)
        return []
