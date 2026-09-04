import os
os.environ["DEMO_MODE"] = "true"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_cited_chat():
    response = client.post("/api/chat", json={"question": "How is the API deployed?"})
    assert response.status_code == 200
    body = response.json()
    assert body["agent"] == "technical"
    assert body["citations"]

