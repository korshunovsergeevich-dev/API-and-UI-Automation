import json
from typing import Any, Dict

import pytest
import requests

from config import BASE_URL, ENDPOINTS, PAYLOAD_GET_EVENTS
from config import PAYLOAD_CREATE_PERSONAL, PAYLOAD_UPDATE_PERSONAL


def _make_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
) -> requests.Response:
    data = json.dumps(payload)
    return requests.request(method, url, headers=headers, data=data)


@pytest.mark.parametrize(
    "endpoint_key, payload",
    [
        ("events", PAYLOAD_GET_EVENTS),
        ("create_personal", PAYLOAD_CREATE_PERSONAL),
        ("update_personal", PAYLOAD_UPDATE_PERSONAL),
    ],
    ids=["get_events", "create_personal", "update_personal"],
)
def test_schedule_endpoints(headers, endpoint_key, payload):
    url = f"{BASE_URL}{ENDPOINTS[endpoint_key]}"
    response = _make_request("POST", url, headers, payload)

    assert response.status_code in (
        200, 201), f"Unexpected status: {response.status_code}"

    try:
        response_json = response.json()
    except ValueError:
        pytest.fail("Response is not valid JSON")

    assert isinstance(response_json, (dict, list))


def test_update_personal_specific(headers):
    url = f"{BASE_URL}{ENDPOINTS['update_personal']}"
    response = _make_request("POST", url, headers, PAYLOAD_UPDATE_PERSONAL)

    assert response.status_code in (
        200, 204), f"Update failed: {response.status_code}"

    try:
        data = response.json()
        assert isinstance(data, (dict, list))
    except ValueError:
        if response.status_code != 204:
            pytest.fail("Expected JSON or 204 No Content")
