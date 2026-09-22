"""Tests for validation failures and error handling."""


def test_empty_message_returns_422(client):
    response = client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422


def test_whitespace_only_message_returns_422(client):
    response = client.post("/api/v1/chat", json={"message": "   "})
    assert response.status_code == 422


def test_invalid_temperature_returns_422(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "temperature": 5.0},  # max allowed is 2.0
    )
    assert response.status_code == 422


def test_invalid_max_tokens_returns_422(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "max_tokens": -10},
    )
    assert response.status_code == 422


def test_unsupported_model_returns_422(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello", "model": "not-a-real-model"},
    )
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_model"


def test_missing_message_field_returns_422(client):
    # message is required -- omitting it entirely should fail validation
    response = client.post("/api/v1/chat", json={})
    assert response.status_code == 422