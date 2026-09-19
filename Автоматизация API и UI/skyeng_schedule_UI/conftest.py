import os
import pytest
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Загружаем переменные окружения (SKYENG_USERNAME, SKYENG_PASSWORD) из .env
load_dotenv()


@pytest.fixture(scope="session")
def driver():
    options = Options()
    options.add_argument("--start-maximized")
    # options.add_argument("--headless")  # раскомментируй, если нужен headless

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture
def auth_data():
    username = os.getenv("SKYENG_USERNAME", "test.tst317@skyeng.ru")
    password = os.getenv("SKYENG_PASSWORD", "Abc1234567890")
    return {"username": username, "password": password}
