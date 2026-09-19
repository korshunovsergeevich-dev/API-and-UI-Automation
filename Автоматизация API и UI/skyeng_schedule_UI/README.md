skyeng_schedule_UI/
├── .env                    # Логин и пароль 
├── .gitignore
├── conftest.py             # Общие фикстуры 
├── requirements.txt        # Зависимости проекта
├── test_create_event.py    # Проект

Запуска теста:
```bash
pytest -v test_create_event.py
```
Прогон теста через Allure-report:
```bash
- pytest --alluredir=allure-results
- pytest --alluredir=allure-results --clean-alluredir
- allure serve allure-results
```
## Что проверяет тест

### Тестирование UI проекта (`test_create_event.py`)
- Авторизация профиля
- Создание личного события
- Изменение даты личного события
- Изменение времени личного события
- Удаление личного события