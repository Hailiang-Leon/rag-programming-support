from fastapi.testclient import TestClient

from src.backend.api import main as api_main


client = TestClient(api_main.app)


def test_frontend_homepage_is_served():
    response = client.get("/")

    assert response.status_code == 200
    assert "Source-Grounded RAG Support" in response.text
    assert "Programming Learning Assistant" in response.text
    assert "/static/app.js" in response.text


def test_frontend_javascript_is_served():
    response = client.get("/static/app.js")

    assert response.status_code == 200
    assert "fetch" in response.text
    assert "/ask" in response.text
