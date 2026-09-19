skyeng-api-tests/
├── .env                    # токен авторизации (не попадает в Git)
├── .gitignore
├── requirements.txt        # зависимости проекта
├── config.py              # настройки и тестовые данные
├── conftest.py             # общие фикстуры (заголовки с токеном)
├── test_positive_schedule.py   # позитивные тесты
└── test_negative_schedule.py   # негативные тесты

Все тесты:
```bash
pytest -v
```

Только позитивные:
```bash
pytest -v test_positive_schedule.py
```

Только негативные:
```bash
pytest -v test_negative_schedule.py
```

## Что проверяют тесты

### Позитивные (`test_positive_schedule.py`)
- Получение событий расписания за период
- Создание персонального события
- Обновление персонального события

### Негативные (`test_negative_schedule.py`)
- Создание события с пустым названием (`title=""`) — ожидается ошибка валидации
- Создание события с названием длиннее 40 символов — ожидается ошибка валидации

## Примечания

- Токен хранится в `.env` и не попадает в Git (см. `.gitignore`).
- Все URL и payload вынесены в `config.py`.
- Общая фикстура `headers` — в `conftest.py`, доступна из всех тестов.

## Прогон тестов через Allure-report

- pytest --alluredir=allure-results
- pytest --alluredir=allure-results --clean-alluredir
- allure serve allure-results