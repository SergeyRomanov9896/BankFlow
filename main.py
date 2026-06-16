import json

from src.bankflow.reports import generate_category_report
from src.bankflow.services import search_by_phone, search_transactions
from src.bankflow.views import generate_main_page_json


def main() -> None:
    print("=" * 60)
    print("Тест главной страницы")
    print("=" * 60)

    test_date = "2020-05-20 14:30:00"
    result = generate_main_page_json(test_date)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    print("\n" + "=" * 60)
    print("Тест поиска")
    print("=" * 60)

    search_result = search_transactions("такси")
    print(f"Найдено транзакций: {search_result['count']}")
    if search_result["results"]:
        print("Первые 3 результата:")
        for item in search_result["results"][:3]:
            print(f"  {item['date']}: {item['amount']} руб. - {item['description']}")

    print("\n" + "=" * 60)
    print("Тест поиска по телефону")
    print("=" * 60)

    phone_result = search_by_phone("+7 (900) 000-00-00")
    print(f"Найдено транзакций: {phone_result['count']}")
    if phone_result["results"]:
        for item in phone_result["results"][:3]:
            print(f"  {item['date']}: {item['amount']} руб. - {item['description']}")

    print("\n" + "=" * 60)
    print("Тест отчета по категории")
    print("=" * 60)

    report = generate_category_report("Супермаркеты", "2020-05-20")
    print(report)


if __name__ == "__main__":
    main()
