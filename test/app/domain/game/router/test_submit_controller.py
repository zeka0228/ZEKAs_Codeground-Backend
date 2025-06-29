from unittest.mock import patch
from fastapi.testclient import TestClient
from src.app.main import app

client = TestClient(app)

@patch("src.app.domain.game.service.game_service.evaluate_code", return_value={"result": "correct", "detail": []})
def test_submit_correct(mock_eval):
    data = {"language": "python", "code": "print('hi')"}
    response = client.post("/api/v1/game/submit", json=data)
    assert response.status_code == 200
    assert response.json() == {"result": "correct", "detail": []}
    mock_eval.assert_called_once_with("python", "print('hi')")

@patch("src.app.domain.game.service.game_service.evaluate_code", return_value={"result": "wrong", "detail": []})
def test_submit_wrong(mock_eval):
    data = {"language": "python", "code": "print(\"error\")"}
    response = client.post("/api/v1/game/submit", json=data)
    assert response.status_code == 200
    assert response.json()["result"] == "wrong"
    mock_eval.assert_called_once()
