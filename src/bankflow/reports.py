import logging
import os
from collections.abc import Callable
from typing import Any

import pandas as pd

from .utils import load_transactions_from_excel, prepare_dataframe

# Logging setup
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("bankflow.reports")
file_h = logging.FileHandler("logs/reports.log", mode="a", encoding="utf-8")
fmt = logging.Formatter("%(asctime)s | %(filename)s | %(levelname)s | %(message)s")
file_h.setFormatter(fmt)
logger.addHandler(file_h)
logger.setLevel(logging.INFO)


def save_report(filename: str | None = None) -> Callable[..., Any]:
    """Декоратор, сохраняющий результат функции в CSV-файл.

    Args:
        filename: Имя файла для сохранения. Если None, формируется
            автоматически как ``report_<func_name>.csv``.

    Поведение:
        - Если результат функции — `pandas.DataFrame`, он сохраняется
          в CSV напрямую.
        - Если результат — `dict`, он преобразуется в однострочный
          `DataFrame` и сохраняется.
        - При ошибке сохранения логируется ошибка; исключение не пробрасывается.

    Возвращает:
        Callable: Декорированную функцию с тем же интерфейсом.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info("Вызов функции отчёта: %s", func.__name__)
            result = func(*args, **kwargs)

            # Определяем имя файла
            file_name = filename if filename is not None else f"report_{func.__name__}.csv"

            # Создаем папку reports если её нет
            os.makedirs("reports", exist_ok=True)
            file_path = os.path.join("reports", file_name)

            # Сохраняем в CSV
            try:
                if isinstance(result, pd.DataFrame):
                    result.to_csv(file_path, index=False, encoding="utf-8")
                elif isinstance(result, dict):
                    pd.DataFrame([result]).to_csv(file_path, index=False, encoding="utf-8")
                logger.info("Отчёт %s сохранён в %s", func.__name__, file_path)
            except Exception:
                logger.exception("Ошибка сохранения отчёта %s в %s", func.__name__, file_path)

            return result

        return wrapper

    return decorator


@save_report()
def spending_by_category(transactions: pd.DataFrame, category: str, date: str | None = None) -> pd.DataFrame:
    """Формирует отчёт по расходам для заданной категории за 3 предыдущих месяца.

    Аргументы:
        transactions: `DataFrame` с транзакциями. Ожидаются колонки
            "Дата операции", "Категория" и "Сумма платежа".
        category: Название категории для фильтрации.
        date: Конечная дата периода (строка или `datetime`). Если None,
            используется текущая дата.

    Возвращает:
        `DataFrame` с колонками "Месяц" и "Сумма". Если данных нет — пустой `DataFrame`.

    Логирование:
        Записывает начало формирования отчёта и случаи отсутствия данных.
    """
    logger.info("spending_by_category: category=%s, date=%s", category, date)
    if transactions.empty:
        logger.info("spending_by_category: пустой DataFrame входных транзакций")
        return pd.DataFrame()

    # Если дата не передана, используем текущую
    if date is None:
        target_date = pd.Timestamp.now()
    else:
        target_date = pd.to_datetime(date)

    # Начало периода (3 месяца назад)
    start_date = target_date - pd.DateOffset(months=3)

    # Фильтруем по дате
    mask = (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= target_date)
    filtered_df = transactions[mask]

    # Фильтруем по категории
    category_df = filtered_df[filtered_df["Категория"] == category]

    if category_df.empty:
        logger.info("spending_by_category: нет транзакций для категории %s в периоде", category)
        return pd.DataFrame()

    # Группируем по месяцу и считаем сумму
    category_df = category_df.copy()
    category_df["Месяц"] = category_df["Дата операции"].dt.to_period("M")
    result = category_df.groupby("Месяц")["Сумма платежа"].sum().reset_index()
    result["Месяц"] = result["Месяц"].astype(str)
    result.columns = ["Месяц", "Сумма"]

    logger.info("spending_by_category: сформирован отчёт с %d строк(ой)", len(result))
    return result


def generate_category_report(
    category: str, date: str | None = None, excel_path: str = "data/operations.xlsx"
) -> pd.DataFrame:
    """Обёртка для получения отчёта по категории из файла Excel.

    Загружает транзакции по пути `excel_path`, подготавливает данные и
    вызывает `spending_by_category`.

    Аргументы:
        category: Название категории для отчёта.
        date: Конечная дата периода (строка или `datetime`).
        excel_path: Путь к Excel-файлу с транзакциями.

    Возвращает:
        `DataFrame` — результат `spending_by_category`.
    """
    logger.info("generate_category_report: category=%s, date=%s, path=%s", category, date, excel_path)
    raw_df = load_transactions_from_excel(excel_path)
    df = prepare_dataframe(raw_df)
    result = spending_by_category(df, category, date)
    logger.info("generate_category_report: готово, строк %d", len(result) if isinstance(result, pd.DataFrame) else 0)
    return result
