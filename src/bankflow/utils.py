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


def load_transactions_from_excel(path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Загружает транзакции из Excel и возвращает DataFrame."""
    try:
        df = pd.read_excel(path)
        logger.info(f"Загружено {len(df)} транзакций из {path}")
        return df
    except FileNotFoundError:
        logger.error(f"Файл не найден: {path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Ошибка при чтении файла: {e}")
        return pd.DataFrame()


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Готовит DataFrame к работе: приводит типы данных."""
    if df.empty:
        logger.warning("Передан пустой DataFrame")
        return df

    df_prepared = df.copy()

    if "Дата операции" in df_prepared.columns:
        df_prepared["Дата операции"] = pd.to_datetime(
            df_prepared["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce"
        )
        df_prepared = df_prepared.dropna(subset=["Дата операции"])
        logger.debug(f"После очистки дат: {len(df_prepared)} строк")

    return df_prepared
