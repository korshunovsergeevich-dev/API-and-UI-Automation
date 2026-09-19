import requests

from config import BASE_URL, ENDPOINTS, PAYLOAD_EMPTY_TITLE, PAYLOAD_LONG_TITLE


def test_create_event_without_title(headers):
    url = f"{BASE_URL}{ENDPOINTS['create_personal']}"
    response = requests.post(url, json=PAYLOAD_EMPTY_TITLE, headers=headers)
    body = response.json()

    assert body["data"] is None
    errors = body.get("errors", [])
    title_errors = [e for e in errors if e.get("property") == "title"]
    assert len(title_errors) > 0
    message = title_errors[0]["error"]["message"]
    assert "at least 1" in message


def test_create_event_with_long_title(headers):
    url = f"{BASE_URL}{ENDPOINTS['create_personal']}"
    response = requests.post(url, json=PAYLOAD_LONG_TITLE, headers=headers)
    body = response.json()

    assert body["data"] is None
    errors = body.get("errors", [])
    title_errors = [e for e in errors if e.get("property") == "title"]
    assert len(title_errors) > 0
    message = title_errors[0]["error"]["message"]
    assert "not exceed 40" in message
