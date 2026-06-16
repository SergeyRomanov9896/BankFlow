import pandas as pd

from src.bankflow import services


def test_normalize_phone():
    assert services.normalize_phone("+7 (900) 123-45-67") == "79001234567"
    assert services.normalize_phone("8 900 123 45 67") == "79001234567"


def test_search_transactions(monkeypatch):
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2026-06-01"]),
            "Сумма платежа": [-100],
            "Категория": ["Еда"],
            "Описание": ["Оплата в магазине"],
        }
    )

    monkeypatch.setattr("src.bankflow.services.load_transactions_from_excel", lambda p=None: df)
    monkeypatch.setattr("src.bankflow.services.prepare_dataframe", lambda x: x)

    res = services.search_transactions("оплата")
    assert res["count"] == 1
    assert res["results"][0]["category"] == "Еда"


def test_search_by_phone(monkeypatch):
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2026-06-01"]),
            "Сумма платежа": [-100],
            "Категория": ["Еда"],
            "Описание": ["Оплата +7 900 123-45-67"],
        }
    )

    monkeypatch.setattr("src.bankflow.services.load_transactions_from_excel", lambda p=None: df)
    monkeypatch.setattr("src.bankflow.services.prepare_dataframe", lambda x: x)

    res = services.search_by_phone("+7 900 123 45 67")
    assert res["count"] == 1
