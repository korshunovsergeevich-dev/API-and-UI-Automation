from typing import Any, Dict

# Базовые настройки
BASE_URL = "https://api-teachers.skyeng.ru"

# Эндпоинты
ENDPOINTS = {
    "events": "/v2/schedule/events",
    "create_personal": "/v2/schedule/createPersonal",
    "update_personal": "/v2/schedule/updatePersonal",
}

# Payload для позитивных тестов
PAYLOAD_GET_EVENTS: Dict[str, Any] = {
    "from": "2026-09-16T00:00:00+03:00",
    "till": "2026-09-21T23:59:59+03:00",
    "onlyTypes": [],
}

PAYLOAD_CREATE_PERSONAL: Dict[str, Any] = {
    "backgroundColor": "#FFF7C7",
    "color": "#FAC641",
    "description": "Описание события",
    "title": "Событие 11",
    "startAt": "2026-09-29T19:00:00+03:00",
    "endAt": "2026-09-29T19:30:00+03:00",
}

PAYLOAD_UPDATE_PERSONAL: Dict[str, Any] = {
    "id": 102394825,
    "oldStartAt": "2026-09-29T19:00:00+03:00",
    "backgroundColor": "#FFF7C7",
    "color": "#FAC641",
    "description": "описание 1",
    "title": "название 1",
    "startAt": "2026-09-29T19:00:00+03:00",
    "endAt": "2026-09-29T19:30:00+03:00",
}

# Payload для негативных тестов
PAYLOAD_EMPTY_TITLE: Dict[str, Any] = {
    "backgroundColor": "#FFF7C7",
    "color": "#FAC641",
    "description": "",
    "title": "",
    "startAt": "2026-09-29T19:00:00+03:00",
    "endAt": "2026-09-29T19:30:00+03:00",
}

PAYLOAD_LONG_TITLE: Dict[str, Any] = {
    "backgroundColor": "#FFF7C7",
    "color": "#FAC641",
    "description": "",
    "title": "Исподвыподвертное бесперпектевнячное цифровое событие",
    "startAt": "2026-09-29T19:00:00+03:00",
    "endAt": "2026-09-29T19:30:00+03:00",
}
