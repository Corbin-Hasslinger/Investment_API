DEV_ORIGIN = "http://localhost:5173"


def test_root_returns_ok(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_allowed_development_origin_receives_cors_headers(client) -> None:
    response = client.get("/", headers={"Origin": DEV_ORIGIN})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == DEV_ORIGIN


def test_allowed_development_origin_receives_preflight_headers(client) -> None:
    response = client.options(
        "/",
        headers={
            "Origin": DEV_ORIGIN,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == DEV_ORIGIN
    assert "GET" in response.headers["access-control-allow-methods"]


def test_disallowed_origin_does_not_receive_cors_headers(client) -> None:
    response = client.get("/", headers={"Origin": "http://evil.example"})

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
