"""Tests for GET /api/v1/models"""


def test_list_models_returns_200(client):
    response = client.get("/api/v1/models")
    assert response.status_code == 200


def test_list_models_returns_expected_shape(client):
    response = client.get("/api/v1/models")
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], list)
    assert len(data["models"]) > 0
    assert "id" in data["models"][0]
    assert "description" in data["models"][0]