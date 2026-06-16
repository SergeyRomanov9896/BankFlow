import os

import pandas as pd

from src.bankflow.reports import generate_category_report, save_report, spending_by_category


def test_save_report_decorator(tmp_path):
    # prepare sample data
    df = pd.DataFrame({"Дата операции": pd.to_datetime(["2026-06-01"]), "Сумма платежа": [-100]})

    filename = "test_report.csv"

    @save_report(filename)
    def make_report():
        return df

    # ensure reports dir cleaned
    reports_dir = os.path.join(os.getcwd(), "reports")
    if os.path.exists(os.path.join(reports_dir, filename)):
        os.remove(os.path.join(reports_dir, filename))

    make_report()

    path = os.path.join(reports_dir, filename)
    assert os.path.exists(path)
    # basic content check
    saved = pd.read_csv(path)
    assert "Сумма платежа" in saved.columns

    # cleanup
    os.remove(path)


def test_spending_by_category_empty():
    res = spending_by_category(pd.DataFrame(), "Еда")
    assert res.empty


def test_generate_category_report(monkeypatch):
    df = pd.DataFrame(
        {
            "Дата операции": pd.to_datetime(["2026-04-01", "2026-05-01", "2026-06-01"]),
            "Сумма платежа": [-10, -20, -30],
            "Категория": ["Еда", "Еда", "Прочее"],
        }
    )

    monkeypatch.setattr("src.bankflow.reports.load_transactions_from_excel", lambda p=None: df)
    monkeypatch.setattr("src.bankflow.reports.prepare_dataframe", lambda x: x)

    result = generate_category_report("Еда", "2026-06-01")
    assert not result.empty
    assert "Месяц" in result.columns
