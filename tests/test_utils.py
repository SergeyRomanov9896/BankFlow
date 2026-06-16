import pandas as pd

from src.bankflow.utils import load_transactions_from_excel, prepare_dataframe


def test_load_transactions_from_excel_success(monkeypatch):
    called = {}

    def fake_read_excel(path):
        called["path"] = path
        return pd.DataFrame([{"Дата операции": "01.06.2026 12:00:00", "Сумма платежа": -100}])

    monkeypatch.setattr("pandas.read_excel", fake_read_excel)

    df = load_transactions_from_excel("dummy.xlsx")
    assert isinstance(df, pd.DataFrame)
    assert called["path"] == "dummy.xlsx"


def test_prepare_dataframe_converts_dates():
    df = pd.DataFrame(
        {
            "Дата операции": ["01.06.2026 12:00:00", "invalid"],
            "Сумма платежа": [100, -50],
        }
    )

    res = prepare_dataframe(df)
    assert "Дата операции" in res.columns
    # invalid row should be dropped
    assert len(res) == 1
    assert pd.api.types.is_datetime64_any_dtype(res["Дата операции"])


def test_prepare_dataframe_empty():
    empty = pd.DataFrame()
    res = prepare_dataframe(empty)
    assert res.empty
