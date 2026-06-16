# BankFlow

Коротко: простой набор утилит для загрузки, пред обработки и агрегирования банковских транзакций из Excel-файлов, формирования отчётов и вспомогательных поисковых сервисов.

---

## 1. Описание проекта

Проект предоставляет функциональность для работы с транзакциями, представленными в табличных файлах (Excel):

- загрузка и подготовка данных (`src.bankflow.utils`);
- фильтрация по дате, вычисление агрегатов и формирование данных для «главной страницы» (`src.bankflow.views`);
- поисковые сервисы по тексту и по телефонным номерам в описании транзакций (`src.bankflow.services`);
- генерация и сохранение CSV-отчётов по категориям (`src.bankflow.reports`).

Цель: дать минимальный, удобный набор функций для анализа месячных/квартальных расходов, построения простых статистик и экспорта отчётов.

---

## 2. Технологии и стек

- Python 3.10+ (рекомендуется 3.12)
- Библиотеки:
	- `pandas` — работа с табличными данными
	- `openpyxl` — чтение Excel (используется `pandas.read_excel`)
	- `requests` — HTTP-запросы (получение курсов валют и цен акций)
- Тестирование: `pytest`
- Логирование: встроенный `logging`, логи пишутся в папки `logs/` и `reports/`

Файловая структура (важные модули):
- `src/bankflow/utils.py` — загрузка/подготовка данных
- `src/bankflow/views.py` — агрегаты и формирование JSON-ответа
- `src/bankflow/services.py` — поиск по описанию и по телефонам
- `src/bankflow/reports.py` — декоратор сохранения отчётов и генерация отчетов по категориям
- `main.py` — (точка запуска CLI/демо) запуск основных сценариев

---

## 3. Инструкция по установке

1. Клонировать репозиторий:
```bash
git clone https://github.com/SergeyRomanov9896/BankFlow.git
cd BankFlow
```

2. Рекомендуется создать виртуальное окружение и активировать его:
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# Unix / macOS
source .venv/bin/activate
```

3. Установить зависимости:
```bash
poetry install
```
- Иначе установить минимально требуемые пакеты:
```bash
pip install pandas openpyxl requests pytest
```

Примечание: `pandas.read_excel` для `.xlsx` требует `openpyxl`.

---

## 4. Как запустить проект

```bash
python main.py
```

- Запуск отдельных функций (интерактивно в REPL или скрипте):

Пример: сгенерировать данные «главной страницы» для даты
```python
from src.bankflow.views import generate_main_page_json

resp = generate_main_page_json('2026-06-10')
print(resp['greeting'])
print(resp['cards'])
```

- Запустить тесты:
```bash
pytest -q
```

Логи пишутся в `logs/` (файлы `views.log`, `services.log`, `reports.log`).

---

## 5. Примеры использования

1) Загрузка и подготовка транзакций (из `src.bankflow.utils`):
```python
from src.bankflow.utils import load_transactions_from_excel, prepare_dataframe

df = load_transactions_from_excel('data/operations.xlsx')  # pd.DataFrame
df = prepare_dataframe(df)  # даты конвертированы, некорректные строки удалены
```

2) Формирование данных для главной страницы (агрегаты):
```python
from src.bankflow.views import generate_main_page_json

data = generate_main_page_json('2026-06-10', excel_path='data/operations.xlsx')
# data содержит: greeting, cards, top_5_transactions, expenses_and_income,
# top_categories, cashback_by_category, currency_rates, stock_prices
```

3) Поиск по описанию и по телефону (в `src.bankflow.services`):
```python
from src.bankflow.services import search_transactions, search_by_phone

res = search_transactions('оплата', excel_path='data/operations.xlsx')
print(res['count'], res['results'])

phone_res = search_by_phone('+7 900 123 45 67', excel_path='data/operations.xlsx')
print(phone_res['count'])
```

4) Генерация CSV-отчёта по категории (в `src.bankflow.reports`):
```python
from src.bankflow.reports import generate_category_report

# сгенерирует DataFrame и сохранит CSV через декоратор save_report()
df_report = generate_category_report('Еда', date='2026-06-01', excel_path='data/operations.xlsx')
print(df_report)
# CSV будет записан в папку reports/, имя файла по умолчанию report_spending_by_category.csv
```
