from uuid import UUID

from atlas_api.di import get_current_user
from atlas_api.schemas.user import CurrentUserRead


def test_get_current_user_uses_dependency_override(client, override_dependency) -> None:
    override_dependency(
        get_current_user,
        lambda: CurrentUserRead(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            email="override-user@atlas.local",
        ),
    )

    response = client.get("/users/me")

    assert response.status_code == 200
    assert response.json() == {
        "id": "22222222-2222-2222-2222-222222222222",
        "email": "override-user@atlas.local",
    }
