import logging
import os
import re

from utils import load_transactions_from_excel, prepare_dataframe

# Logging setup
os.makedirs("logs", exist_ok=True)
logger = logging.getLogger("bankflow.services")
file_h = logging.FileHandler("logs/services.log", mode="w", encoding="utf-8")
fmt = logging.Formatter("%(asctime)s | %(filename)s | %(levelname)s | %(message)s")
file_h.setFormatter(fmt)
logger.addHandler(file_h)
logger.setLevel(logging.INFO)


def search_transactions(query: str, excel_path: str = "data/operations.xlsx") -> dict:
    """Ищет транзакции по текстовому запросу.

    Функция ищет совпадения по колонкам "Описание" и "Категория" (регистронезависимо)
    и возвращает список найденных операций.

    Args:
        query: Строка поиска (поддерживается как обычный текст).
        excel_path: Путь к Excel-файлу с транзакциями.

    Returns:
        dict: Словарь с ключами `query`, `results` (список совпадений) и `count`.

    Логирование:
        Записывает начало поиска и возвращает информацию о пустом результате.
    """
    logger.info("search_transactions: query=%s, excel_path=%s", query, excel_path)
    raw_df = load_transactions_from_excel(excel_path)
    df = prepare_dataframe(raw_df)

    if df.empty:
        logger.info("search_transactions: пустой DataFrame для запроса %s", query)
        return {"query": query, "results": [], "count": 0}

    mask = df["Описание"].str.contains(query, case=False, na=False) | df["Категория"].str.contains(
        query, case=False, na=False
    )
    results_df = df[mask]

    results = []
    for _, row in results_df.iterrows():
        results.append(
            {
                "date": row["Дата операции"].strftime("%d.%m.%Y"),
                "amount": round(row["Сумма платежа"], 2),
                "category": row["Категория"],
                "description": row["Описание"],
            }
        )

    return {
        "query": query,
        "results": results,
        "count": len(results),
    }


def normalize_phone(phone: str) -> str:
    """Нормализует российский телефонный номер в формат без цифр и с префиксом 7.

    Преобразования:
    - Удаляются все нецифровые символы.
    - Номер, начинающийся с `8` и длиной 11 символов, конвертируется в `7...`.

    Args:
        phone: Входная строка с номером телефона.

    Returns:
        str: Нормализованный набор цифр (например, "79001234567").
    """
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    return digits


def search_by_phone(phone_query: str, excel_path: str = "data/operations.xlsx") -> dict:
    """Ищет транзакции по телефонному номеру, найденному в описании.

    Алгоритм:
    - Загружает и подготавливает `DataFrame` транзакций.
    - Нормализует запросный номер (см. `normalize_phone`).
    - Ищет телефонные шаблоны в тексте поля "Описание" и сравнивает
      нормализованные цифры.

    Args:
        phone_query: Номер телефона в произвольном формате.
        excel_path: Путь к Excel-файлу с транзакциями.

    Returns:
        dict: Словарь с ключами `query`, `results` (список совпадений) и `count`.

    Логирование:
        Логирует начало поиска и количество найденных записей.
    """
    logger.info("search_by_phone: phone_query=%s, excel_path=%s", phone_query, excel_path)
    raw_df = load_transactions_from_excel(excel_path)
    df = prepare_dataframe(raw_df)

    if df.empty:
        logger.info("search_by_phone: пустой DataFrame для запроса %s", phone_query)
        return {"query": phone_query, "results": [], "count": 0}

    normalized_query = normalize_phone(phone_query)

    phone_pattern = re.compile(
        r"(?:\+?7[\s\-()]?\d{3}[\s\-()]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
        r"|(?:8[\s\-()]?\d{3}[\s\-()]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2})"
    )

    results = []
    for _, row in df.iterrows():
        description = str(row["Описание"])
        phones_found = phone_pattern.findall(description)
        for phone in phones_found:
            if normalize_phone(phone) == normalized_query:
                results.append(
                    {
                        "date": row["Дата операции"].strftime("%d.%m.%Y"),
                        "amount": round(row["Сумма платежа"], 2),
                        "category": row["Категория"],
                        "description": description,
                    }
                )
                break

    logger.info("search_by_phone: найдено %d результатов для %s", len(results), phone_query)
    return {
        "query": phone_query,
        "results": results,
        "count": len(results),
    }


if __name__ == "__main__":
    print()
