from fastapi.testclient import TestClient
from fraud.main import app

client = TestClient(app)


def test_high_and_low():
    assert client.post("/score", json={'amount': 900, 'foreign': 1, 'velocity': 8}).json()["label"]
    high = client.post("/score", json={'amount': 900, 'foreign': 1, 'velocity': 8}).json()
    low = client.post("/score", json={'amount': 12, 'foreign': 0, 'velocity': 1}).json()
    assert high["label"] != low["label"]
    assert high["score"] > low["score"]


def test_missing_is_refused():
    body = dict({'amount': 900, 'foreign': 1, 'velocity': 8})
    body.pop("amount")
    assert client.post("/score", json=body).status_code == 422
