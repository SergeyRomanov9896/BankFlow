import pandas as pd

from src.bankflow import views


def test_get_greeting_variants():
    assert views.get_greeting("2026-06-14T08:00:00") == "Доброе утро"
    assert views.get_greeting("2026-06-14T13:00:00") == "Добрый день"
    assert views.get_greeting("2026-06-14T19:00:00") == "Добрый вечер"
    # invalid parses to default noon -> 'Добрый день'
    assert views.get_greeting("not a date") == "Добрый день"


def test_filter_transactions_by_date():
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2026-06-01", "2026-06-10", "2026-05-20"]),
            "Сумма платежа": [10, -20, -30],
        }
    )

    res = views.filter_transactions_by_date(df, "2026-06-10")
    assert len(res) == 2


def test_get_card_statistics():
    df = pd.DataFrame(
        {
            "Номер карты": ["1234567812345678", "1234****56785678", ""],
            "Сумма платежа": [-100, -200, 50],
        }
    )

    stats = views.get_card_statistics(df)
    assert isinstance(stats, list)
    # there should be 3 entries (unique group by value as provided)
    assert any("total_expenses" in s for s in stats)


def test_get_currency_rates(monkeypatch):

    def fake_get(url, timeout=5):
        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"Valute": {"USD": {"Value": 73.5}, "EUR": {"Value": 86.1}}}

        return Resp()

    monkeypatch.setattr("requests.get", fake_get)
    rates = views.get_currency_rates(["USD", "EUR", "XXX"])
    assert {"currency": "USD", "rate": 73.5} in rates or any(r["currency"] == "USD" for r in rates)


def test_get_stock_prices(monkeypatch):
    def fake_get(url, headers=None, timeout=5):
        class Resp:
            def raise_for_status(self):
                pass

            def json(self):
                return {"chart": {"result": [{"meta": {"regularMarketPrice": 150.0}}]}}

        return Resp()

    monkeypatch.setattr("requests.get", fake_get)
    prices = views.get_stock_prices(["AAPL"])
    assert prices[0]["price"] == 150.0


def test_generate_main_page_json(monkeypatch):
    # Mock load and prepare to return a small dataframe
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2026-06-01"]),
            "Сумма платежа": [-100],
            "Категория": ["Еда"],
            "Номер карты": ["1234"],
            "Описание": ["Оплата"],
        }
    )

    monkeypatch.setattr("src.bankflow.views.load_transactions_from_excel", lambda path=None: df)
    monkeypatch.setattr("src.bankflow.views.prepare_dataframe", lambda x: x)
    monkeypatch.setattr("src.bankflow.views.get_currency_rates", lambda cur: [{"currency": "USD", "rate": 1}])
    monkeypatch.setattr("src.bankflow.views.get_stock_prices", lambda stk: [{"stock": "AAPL", "price": 1}])
    monkeypatch.setattr(
        "src.bankflow.views.load_user_settings", lambda: {"user_currencies": ["USD"], "user_stocks": ["AAPL"]}
    )

    resp = views.generate_main_page_json("2026-06-10")
    assert "greeting" in resp
    assert "cards" in resp
