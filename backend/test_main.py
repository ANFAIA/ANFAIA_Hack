import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "OmniBot Proxy is running"}

def test_create_discovery():
    embedding = [0.1] * 768
    response = client.post(
        "/discoveries",
        json={
            "description": "Saw a cool dog",
            "type": "Pet",
            "embedding": embedding
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "id" in response.json()

def test_create_discovery_invalid_embedding():
    embedding = [0.1] * 10 # Invalid length
    response = client.post(
        "/discoveries",
        json={
            "description": "Saw a cool dog",
            "type": "Pet",
            "embedding": embedding
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Embedding must be 768 dimensions"

def test_get_discoveries():
    response = client.get("/discoveries")
    assert response.status_code == 200
    assert "data" in response.json()
    assert isinstance(response.json()["data"], list)

def test_websocket():
    with client.websocket_connect("/ws") as websocket:
        websocket.send_text("Hello OmniBot")
        data = websocket.receive_text()
        assert data == "Message text was: Hello OmniBot"
