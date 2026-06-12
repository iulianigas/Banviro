def test_ai_status() -> None:
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    response = client.get("/api/v1/ai/status")
    assert response.status_code == 200
    data = response.json()
    assert "ai_enabled" in data
    assert "ollama_available" in data
    assert data.get("agent") == "langgraph"
    assert data.get("streaming") is True
    assert "phoenix_enabled" in data
    assert "phoenix_tracing_active" in data
