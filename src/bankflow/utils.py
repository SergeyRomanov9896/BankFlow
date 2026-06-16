import logging
import os

import pandas as pd

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("bankflow.utils")
file_h = logging.FileHandler("logs/utils.log", mode="w", encoding="utf-8")
fmt = logging.Formatter("%(asctime)s | %(filename)s | %(levelname)s | %(message)s")

file_h.setFormatter(fmt)
logger.addHandler(file_h)
logger.setLevel(logging.DEBUG)


def load_transactions_from_excel(path: str = "data/operations.xlsx") -> pd.DataFrame:
    """Загружает транзакции из Excel и возвращает `DataFrame`.

    Args:
        path: Путь к Excel-файлу. По умолчанию ``data/operations.xlsx``.

    Returns:
        pd.DataFrame: Содержимое Excel в виде `DataFrame`.
        В случае ошибки чтения возвращается пустой `DataFrame`.

    Логирование:
        При успешной загрузке в лог пишется количество строк, при ошибке
        — сообщение об исключении.
    """
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
    """Подготавливает `DataFrame` к дальнейшей обработке.

    Операции:
    - Если `df` пустой — возвращается тот же пустой `DataFrame` и логируется
      предупреждение.
    - Копируется входной `DataFrame` для избегания побочных эффектов.
    - Если есть колонка ``"Дата операции"``, она конвертируется в
      тип ``datetime`` по формату ``"%d.%m.%Y %H:%M:%S"``. При некорректных
      значениях ставится ``NaT`` и такие строки удаляются.

    Args:
        df: Входной `pd.DataFrame` с транзакциями.

    Returns:
        pd.DataFrame: Подготовленный `DataFrame` с корректными типами данных.
    """
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
