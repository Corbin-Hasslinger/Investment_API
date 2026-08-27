def test_root_returns_ok(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
