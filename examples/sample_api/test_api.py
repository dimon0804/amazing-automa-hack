from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


def test_health() -> None:
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}


def test_sum() -> None:
    response = client.get('/sum', params={'a': 2, 'b': 3})
    assert response.status_code == 200
    assert response.json()['result'] == 5
