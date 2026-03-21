import itertools
import json

import pytest


@pytest.fixture(autouse=True)
def allow_test_hosts(settings):
    settings.ALLOWED_HOSTS = ["testserver", "localhost"]


@pytest.fixture
def api_post():
    def _api_post(client, path, payload):
        return client.post(path, data=json.dumps(payload), content_type="application/json")

    return _api_post


@pytest.fixture
def user_payload_factory():
    counter = itertools.count()

    def _user_payload(prefix="user", password="StrongPass123!"):
        index = next(counter)
        return {
            "email": f"{prefix}-{index}@example.com",
            "password": password,
            "first_name": f"{prefix.capitalize()}Name",
            "last_name": "Testov",
            "patronymic": "Testovich",
            "birth_date": "2000-01-01",
        }

    return _user_payload


@pytest.fixture
def register_and_login(api_post, user_payload_factory):
    def _register_and_login(client, prefix="user"):
        from users.models import User

        payload = user_payload_factory(prefix=prefix)

        register_response = api_post(client, "/api/users/register", payload)
        assert register_response.status_code == 200, register_response.content
        register_body = register_response.json()
        assert register_body["success"] is True
        assert register_body["user"]["email"] == payload["email"]

        user = User.objects.get(email=payload["email"])

        client.logout()

        login_response = api_post(
            client,
            "/api/users/login",
            {"email": payload["email"], "password": payload["password"]},
        )
        assert login_response.status_code == 200, login_response.content
        login_body = login_response.json()
        assert login_body["success"] is True
        assert login_body["user"]["id"] == user.id

        return user, payload

    return _register_and_login


@pytest.fixture
def api_datetime():
    def _api_datetime(value):
        from django.utils import timezone

        return value.astimezone(timezone.get_current_timezone()).strftime("%Y-%m-%dT%H:%M:%S")

    return _api_datetime
