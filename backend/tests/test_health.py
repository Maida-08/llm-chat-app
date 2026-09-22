"""Tests for GET /health"""


def test_health_check_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_returns_healthy_status(client):
    response = client.get("/health")
    assert response.json() == {"status": "healthy"}