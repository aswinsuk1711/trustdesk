import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["DATABASE_URL"] = "sqlite:///./test_trustdesk.db"

from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    with TestClient(app) as client:
        assert client.get("/api/health").status_code == 200


def test_tickets_exist():
    with TestClient(app) as client:
        response = client.get("/api/tickets")
    assert response.status_code == 200
    assert len(response.json()) >= 4


def test_unsafe_ticket_is_escalated():
    with TestClient(app) as client:
        response = client.post("/api/tickets/TKT-004/triage")
    assert response.status_code == 200
    body = response.json()
    assert body["escalation"] is True


def test_draft_has_citations_for_refund():
    with TestClient(app) as client:
        response = client.post("/api/tickets/TKT-001/draft")
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]


def test_eval_runs():
    with TestClient(app) as client:
        response = client.post("/api/evaluations/run")
    assert response.status_code == 200
    assert "metrics" in response.json()
