import json
import logging
import os
from typing import Any

import pandas as pd
import requests
from utils import load_transactions_from_excel, prepare_dataframe

os.makedirs("logs", exist_ok=True)

logger = logging.getLogger("bankflow.views")
file_h = logging.FileHandler("logs/views.log", mode="w", encoding="utf-8")
fmt = logging.Formatter("%(asctime)s | %(filename)s | %(levelname)s | %(message)s")
file_h.setFormatter(fmt)
logger.addHandler(file_h)
logger.setLevel(logging.DEBUG)

# Путь к user_settings.json (в корне проекта)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SETTINGS_PATH = os.path.join(BASE_DIR, "config", "user_settings.json")


def load_user_settings() -> dict[str, Any]:
    """Загружает пользовательские настройки из файла `user_settings.json`.

    Функция пытается прочитать JSON-файл по пути, заданному в
    переменной `SETTINGS_PATH`. Если файла нет или он некорректен,
    возвращается набор настроек по умолчанию.

    Returns:
        dict[str, Any]: Словарь с ключами `user_currencies` и `user_stocks`.

    Логирование:
        Ошибки чтения и отсутствие файла логируются через `logger`.
    """
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
        logger.warning("Файл %s не найден, используем настройки по умолчанию", SETTINGS_PATH)
        return default_settings
    except json.JSONDecodeError:
        logger.error("Ошибка чтения %s, используем настройки по умолчанию", SETTINGS_PATH)
        return default_settings


def get_greeting(date_time_str: str) -> str:
    """Возвращает строку-приветствие по времени.

    Args:
        date_time_str: Строка, парсируемая в дату/время (поддерживает
            форматы, распознаваемые `pandas.to_datetime`).

    Returns:
        str: Одна из строк: "Доброе утро", "Добрый день", "Добрый вечер",
        "Доброй ночи". В случае ошибки парсинга используется полуденное
        время (12:00) и возвращается "Добрый день".
    """
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
    """Фильтрует `DataFrame` по дате: от 1-го числа месяца до `target_date`.

    Args:
        df: `pd.DataFrame` с транзакциями. Ожидается, что колонка с датами
            уже имеет тип `datetime64[ns]` (см. `prepare_dataframe`).
        target_date: Целевая дата (строка или `datetime`), до которой
            включительно проводится фильтрация.
        date_column: Имя колонки с датой в `df` (по умолчанию "Дата операции").

    Returns:
        pd.DataFrame: Отфильтрованный `DataFrame`. При пустом входе возвращается
        тот же пустой `DataFrame`.
    """
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


def get_card_statistics(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Считает агрегированную статистику по картам.

    Для каждой уникальной строки в колонке "Номер карты" вычисляется:
    - последние 4 цифры карты (`last_4_digits`),
    - суммарные расходы (`total_expenses`) — абсолютная сумма всех
      отрицательных значений в колонке "Сумма платежа",
    - примерный кешбэк (`cashback`) как целочисленное деление
      суммы расходов на 100 (1% округлённый вниз).

    Args:
        df: `pd.DataFrame` с колонками "Номер карты" и "Сумма платежа".

    Returns:
        list[dict]: Список словарей со статистикой по каждой карте.
    """
    if df.empty:
        return []

    stats = []

    for card, group in df.groupby("Номер карты"):
        card_str = str(card).strip()
        if "*" in card_str:
            last_4 = card_str.replace("*", "")[-4:]
        elif card_str:
            last_4 = card_str[-4:]
        else:
            last_4 = "Неизвестно"

        expenses = group[group["Сумма платежа"] < 0]["Сумма платежа"].sum()
        total_expenses = abs(expenses)
        cashback = int(total_expenses // 100)

        stats.append(
            {
                "last_4_digits": last_4,
                "total_expenses": round(total_expenses, 2),
                "cashback": cashback,
            }
        )

    return stats


def get_top_5_transactions(df: pd.DataFrame) -> list:
    """Возвращает список до 5-ти крупнейших расходов.

    Args:
        df: `pd.DataFrame` с колонками "Дата операции", "Сумма платежа",
            "Категория" и "Описание".

    Returns:
        list[dict]: Список словарей с ключами `date`, `amount`, `category`,
        `description`. Дата форматируется как `DD.MM.YYYY`.
    """
    expenses_df = df[df["Сумма платежа"] < 0]

    if expenses_df.empty:
        return []

    sorted_df = expenses_df.reindex(expenses_df["Сумма платежа"].abs().sort_values(ascending=False).index).head(5)

    result = []
    for _, row in sorted_df.iterrows():
        result.append(
            {
                "date": row["Дата операции"].strftime("%d.%m.%Y"),
                "amount": round(row["Сумма платежа"], 2),
                "category": row["Категория"],
                "description": row["Описание"],
            }
        )
    return result


def get_currency_rates(currencies: list) -> list[dict[str, Any]]:
    """Получает текущие курсы валют из открытого API Центрального банка РФ.

    Args:
        currencies: Список строк с кодами валют (например, `['USD', 'EUR']`).

    Returns:
        list[dict]: Список словарей вида `{'currency': code, 'rate': value}`.
        При ошибках сети или отсутствии данных для валюты возвращается
        значение `rate: 0.0`.

    Логирование:
        Ошибки сетевых запросов логируются через `logger`.
    """
    rates = []
    if not currencies:
        return rates

    try:
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        valutes = data.get("Valute", {})

        for currency in currencies:
            if currency in valutes:
                rate_value = float(valutes[currency]["Value"])
                rates.append({"currency": currency, "rate": round(rate_value, 2)})
            else:
                rates.append({"currency": currency, "rate": 0.0})

    except requests.RequestException as e:
        logger.error("Ошибка запроса курсов валют: %s", e)
        rates = [{"currency": c, "rate": 0.0} for c in currencies]

    return rates


def get_stock_prices(stocks: list[str]) -> list[dict[str, Any]]:
    """Запрашивает текущие цены акций через неофициальный API Yahoo Finance.

    Args:
        stocks: Список тикеров (например, `['AAPL', 'AMZN']`).

    Returns:
        list[dict]: Список словарей `{'stock': ticker, 'price': value}`.
        В случае ошибки для тикера возвращается цена `1.0` и ошибка логируется.
    """
    prices = []
    if not stocks:
        return prices

    for stock in stocks:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{stock}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            data = response.json()
            price = float(data["chart"]["result"][0]["meta"]["regularMarketPrice"])
            prices.append({"stock": stock, "price": round(price, 2)})
        except Exception as e:
            logger.error("Ошибка получения цены %s: %s", stock, e)
            prices.append({"stock": stock, "price": 1.0})

    return prices


def get_expenses_and_income(df: pd.DataFrame) -> dict[str, int]:
    """Вычисляет суммарные расходы и доходы в целых рублях.

    Args:
        df: `pd.DataFrame` с колонкой "Сумма платежа".

    Returns:
        dict: Словарь с ключами `expenses` и `income` (целые числа).
    """
    if df.empty:
        return {"expenses": 0, "income": 0}

    expenses = int(abs(round(df[df["Сумма платежа"] < 0]["Сумма платежа"].sum())))
    income = int(round(df[df["Сумма платежа"] > 0]["Сумма платежа"].sum()))

    return {"expenses": expenses, "income": income}


def get_top_categories(df: pd.DataFrame, top_n: int = 7) -> list[dict[str, Any]]:
    """Строит рейтинг топ-N категорий расходов и группирует остаток.

    Особые категории `Переводы` и `Снятие наличных` выделяются и добавляются
    в начало результата при наличии.

    Args:
        df: `pd.DataFrame` с колонкой "Категория" и отрицательными
            значениями в "Сумма платежа" для расходов.
        top_n: Количество основных категорий для включения в результат.

    Returns:
        list[dict]: Список словарей вида `{'category': name, 'total': amount}`.
    """
    if df.empty:
        return []

    expenses_df = df[df["Сумма платежа"] < 0].copy()
    if expenses_df.empty:
        return []

    expenses_df["amount"] = expenses_df["Сумма платежа"].abs()

    special_categories = ["Переводы", "Снятие наличных"]
    special = expenses_df[expenses_df["Категория"].isin(special_categories)]
    regular = expenses_df[~expenses_df["Категория"].isin(special_categories)]

    result = []

    if not special.empty:
        for cat, group in special.groupby("Категория"):
            total = int(round(group["amount"].sum()))
            result.append({"category": cat, "total": total})

    if not regular.empty:
        category_totals = regular.groupby("Категория")["amount"].sum().sort_values(ascending=False)

        top_categories = category_totals.head(top_n)
        for idx in range(len(top_categories)):
            cat_name = str(top_categories.index[idx])
            cat_total = float(top_categories.iloc[idx])
            result.append({"category": cat_name, "total": int(round(cat_total))})

        rest = category_totals.iloc[top_n:]
        if not rest.empty:
            rest_total = int(round(rest.sum()))
            result.append({"category": "Остальное", "total": rest_total})

    return result


def get_cashback_by_category(df: pd.DataFrame, top_n: int = 3) -> list[dict[str, Any]]:
    """Вычисляет предполагаемый кешбэк (1% от расходов) для топ-N категорий.

    Args:
        df: `pd.DataFrame` с колонкой "Сумма платежа" и "Категория".
        top_n: Сколько категорий вернуть.

    Returns:
        list[dict]: Список словарей `{'category', 'total_spent', 'cashback'}`.
    """
    if df.empty:
        return []

    expenses_df = df[df["Сумма платежа"] < 0].copy()
    if expenses_df.empty:
        return []

    expenses_df["amount"] = expenses_df["Сумма платежа"].abs()

    category_totals = expenses_df.groupby("Категория")["amount"].sum().sort_values(ascending=False)

    result = []
    for cat, total in category_totals.head(top_n).items():
        cashback = int(total // 100)
        result.append({"category": cat, "total_spent": int(round(total)), "cashback": cashback})

    return result


def generate_main_page_json(
    date_time_str: str,
    excel_path: str = "data/operations.xlsx",
) -> dict[str, Any]:
    """Формирует агрегированный словарь с данными для главной страницы.

    Функция загружает транзакции из Excel, выполняет подготовку данных,
    фильтрацию по дате и рассчитывает набор метрик: приветствие,
    статистику по картам, топ-5 транзакций, суммы расходов/доходов,
    топ-категорий, кешбэк, курсы валют и цены акций.

    Args:
        date_time_str: Целевая дата/время (строка) для фильтрации и приветствия.
        excel_path: Путь к Excel-файлу с транзакциями.

    Returns:
        dict[str, Any]: Словарь с полями:
            - `greeting` (str)
            - `cards` (list)
            - `top_5_transactions` (list)
            - `expenses_and_income` (dict)
            - `top_categories` (list)
            - `cashback_by_category` (list)
            - `currency_rates` (list)
            - `stock_prices` (list)

    Логирование:
        Начало генерации и краткая отладочная информация логируются.
    """
    logger.info("Генерация данных для главной страницы на дату %s", date_time_str)
    raw_df = load_transactions_from_excel(excel_path)
    df = prepare_dataframe(raw_df)

    df_filtered = filter_transactions_by_date(df, date_time_str)

    settings = load_user_settings()

    response = {
        "greeting": get_greeting(date_time_str),
        "cards": get_card_statistics(df_filtered),
        "top_5_transactions": get_top_5_transactions(df_filtered),
        "expenses_and_income": get_expenses_and_income(df_filtered),
        "top_categories": get_top_categories(df_filtered),
        "cashback_by_category": get_cashback_by_category(df_filtered),
        "currency_rates": get_currency_rates(settings["user_currencies"]),
        "stock_prices": get_stock_prices(settings["user_stocks"]),
    }

    logger.debug(
        "Сформирован ответ для главной страницы: %s", {k: v for k, v in response.items() if k in ("greeting",)}
    )
    return response
