"""Tests for POST /api/v1/chat and /api/v1/chat/stream"""


def test_successful_chat_request(client):
    response = client.post(
        "/api/v1/chat",
        json={"message": "Hello, how are you?"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["response"] == "This is a fake response."
    assert data["tokens_used"] == 42
    assert "latency_ms" in data
    assert "model" in data


def test_chat_request_returns_request_id_header(client):
    response = client.post("/api/v1/chat", json={"message": "Hello"})
    assert "X-Request-ID" in response.headers


def test_chat_stream_returns_200(client):
    response = client.post(
        "/api/v1/chat/stream",
        json={"message": "Count to five."},
    )
    assert response.status_code == 200


def test_chat_stream_returns_expected_content(client):
    response = client.post(
        "/api/v1/chat/stream",
        json={"message": "Count to five."},
    )
    # FakeProvider yields these chunks concatenated together
    assert response.text == "This is a fake stream."