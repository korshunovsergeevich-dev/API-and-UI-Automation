import os

import pytest
from dotenv import load_dotenv

load_dotenv()

loaded = load_dotenv()   # вернёт True, если файл найден
print("load_dotenv ->", loaded)
print("cwd ->", os.getcwd())
print("SKYENG_TOKEN ->", repr(os.getenv("SKYENG_TOKEN")))


@pytest.fixture(scope="session")
def headers():
    token = os.getenv("SKYENG_TOKEN")
    return {
        "Content-Type": "application/json",
        "Cookie": f"token_global={token}",
    }
