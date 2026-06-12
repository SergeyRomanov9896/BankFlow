import json
import os
from typing import Any

import pandas as pd

# Путь к user_settings.json (в корне проекта)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(BASE_DIR, "config", "user_settings.json")


def load_user_settings() -> dict[str, Any]:
    """Загружает пользовательские настройки из user_settings.json."""
    default_settings = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
    }

    try:
        with open(SETTINGS_PATH, encoding="utf-8") as f:
            settings = json.load(f)
            if "user_currencies" in settings and "user_stocks" in settings:
                return settings
            return default_settings
    except FileNotFoundError:
        print(f"Файл {SETTINGS_PATH} не найден, используем настройки по умолчанию")
        return default_settings
    except json.JSONDecodeError:
        print(f"Ошибка чтения {SETTINGS_PATH}, используем настройки по умолчанию")
        return default_settings


def get_greeting(date_time_str: str) -> str:
    """Возвращает приветствие в зависимости от часа."""
    try:
        dt = pd.to_datetime(date_time_str)
        hour = dt.hour
    except Exception:
        hour = 12

    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def filter_transactions_by_date(
    df: pd.DataFrame, target_date: str, date_column: str = "Дата операции"
) -> pd.DataFrame:
    """Фильтрует транзакции с 1-го числа месяца по target_date включительно."""
    if df.empty:
        return df

    df_filtered = df.copy()

    # Парсим целевую дату
    target_dt = pd.to_datetime(target_date)

    # Начало месяца: 1-е число в 00:00:00
    start_of_month = target_dt.replace(day=1, hour=0, minute=0, second=0)

    # Конец целевого дня: 23:59:59
    end_of_target_date = target_dt.replace(hour=23, minute=59, second=59)

    # Фильтрация
    mask = (df_filtered[date_column] >= start_of_month) & (df_filtered[date_column] <= end_of_target_date)
    df_filtered = df_filtered[mask]

    return df_filtered
