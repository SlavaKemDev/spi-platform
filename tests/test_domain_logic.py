from datetime import date, timedelta

import pytest
from django.utils import timezone

from events.models import Event, EventRegistration
from events.regform import validate_form_data, validate_form_schema
from organizations.models import Organization, OrganizationMember
from users.models import University, User


pytestmark = pytest.mark.django_db


def test_validate_form_schema_accepts_full_supported_schema():
    schema = [
        {"name": "name", "label": "Name", "type": "text", "required": True},
        {"name": "bio", "label": "Bio", "type": "textarea", "required": False},
        {"name": "grade", "label": "Grade", "type": "number", "required": True},
        {
            "name": "track",
            "label": "Track",
            "type": "select",
            "required": True,
            "options": ["AI", "Web"],
        },
        {"name": "rules", "label": "Rules", "type": "checkbox", "required": True},
    ]

    is_valid, error = validate_form_schema(schema)

    assert is_valid is True
    assert error == ""


@pytest.mark.parametrize(
    ("schema", "expected_error"),
    [
        (
            [{"name": "track", "label": "Track", "type": "select", "required": True}],
            'необходим непустой список "options"',
        ),
        (
            [
                {"name": "dup", "label": "First", "type": "text", "required": True},
                {"name": "dup", "label": "Second", "type": "text", "required": False},
            ],
            'дублирующийся "name" "dup"',
        ),
        (
            [{"label": "Broken", "type": "text", "required": True}],
            'отсутствует обязательный ключ "name"',
        ),
    ],
)
def test_validate_form_schema_rejects_invalid_definitions(schema, expected_error):
    is_valid, error = validate_form_schema(schema)

    assert is_valid is False
    assert expected_error in error


def test_validate_form_data_rejects_unknown_fields_and_bad_values():
    schema = [
        {"name": "motivation", "label": "Motivation", "type": "textarea", "required": True},
        {"name": "experience", "label": "Experience", "type": "number", "required": False},
        {
            "name": "track",
            "label": "Track",
            "type": "select",
            "required": True,
            "options": ["AI", "Web"],
        },
        {"name": "subscribe", "label": "Subscribe", "type": "checkbox", "required": False},
    ]

    assert validate_form_data(
        {
            "motivation": "Ready to join",
            "experience": 3,
            "track": "AI",
            "subscribe": True,
        },
        schema,
    ) == (True, "")

    missing_required = validate_form_data({"track": "AI"}, schema)
    assert missing_required[0] is False
    assert 'Motivation' in missing_required[1]

    invalid_select = validate_form_data({"motivation": "Go", "track": "Data"}, schema)
    assert invalid_select[0] is False
    assert 'недопустимое значение "Data"' in invalid_select[1]

    unknown_field = validate_form_data(
        {"motivation": "Go", "track": "AI", "extra": "value"},
        schema,
    )
    assert unknown_field[0] is False
    assert 'Неизвестное поле "extra"' == unknown_field[1]


def test_event_status_property_covers_all_time_windows():
    organization = Organization.objects.create(name="Status Org", description="")
    now = timezone.now()

    cases = {
        "upcoming": {
            "registration_start": now + timedelta(days=1),
            "registration_end": now + timedelta(days=2),
            "event_start": now + timedelta(days=3),
            "event_end": now + timedelta(days=4),
        },
        "registration_open": {
            "registration_start": now - timedelta(days=1),
            "registration_end": now + timedelta(days=1),
            "event_start": now + timedelta(days=2),
            "event_end": now + timedelta(days=3),
        },
        "registration_closed": {
            "registration_start": now - timedelta(days=3),
            "registration_end": now - timedelta(days=1),
            "event_start": now + timedelta(days=1),
            "event_end": now + timedelta(days=2),
        },
        "ongoing": {
            "registration_start": now - timedelta(days=4),
            "registration_end": now - timedelta(days=2),
            "event_start": now - timedelta(hours=1),
            "event_end": now + timedelta(hours=1),
        },
        "past": {
            "registration_start": now - timedelta(days=5),
            "registration_end": now - timedelta(days=4),
            "event_start": now - timedelta(days=3),
            "event_end": now - timedelta(days=2),
        },
    }

    for expected_status, dates in cases.items():
        event = Event(
            title=f"{expected_status} event",
            description="Status coverage",
            organization=organization,
            registration_start=dates["registration_start"],
            registration_end=dates["registration_end"],
            event_start=dates["event_start"],
            event_end=dates["event_end"],
            location="Campus",
            format=Event.Format.OFFLINE,
        )

        assert event.status == expected_status


def test_user_manager_and_model_strings():
    with pytest.raises(ValueError, match="Email is required"):
        User.objects.create_user(
            email="",
            password="StrongPass123!",
            first_name="No",
            last_name="Email",
            patronymic="Case",
            birth_date=date(2000, 1, 1),
        )

    university = University.objects.create(name="Tech University", email_domain="tech.example.com")
    user = User.objects.create_user(
        email="member@example.com",
        password="StrongPass123!",
        first_name="Member",
        last_name="User",
        patronymic="Testovich",
        birth_date=date(2000, 1, 1),
        university=university,
    )
    superuser = User.objects.create_superuser(
        email="admin@example.com",
        password="StrongPass123!",
        first_name="Admin",
        last_name="User",
        patronymic="Rootovich",
        birth_date=date(1999, 1, 1),
    )
    organization = Organization.objects.create(name="Model Org", description="Model coverage")
    membership = OrganizationMember.objects.create(
        organization=organization,
        user=user,
        is_admin=True,
    )
    event = Event.objects.create(
        title="Model Event",
        description="Event for __str__ coverage",
        organization=organization,
        registration_start=timezone.now() - timedelta(days=1),
        registration_end=timezone.now() + timedelta(days=1),
        event_start=timezone.now() + timedelta(days=2),
        event_end=timezone.now() + timedelta(days=3),
        location="Hall A",
        format=Event.Format.OFFLINE,
    )
    registration = EventRegistration.objects.create(user=user, event=event, form_answer={})

    assert str(university) == "Tech University"
    assert str(user) == "member@example.com"
    assert superuser.is_staff is True
    assert superuser.is_superuser is True
    assert str(organization) == "Model Org"
    assert "member@example.com" in str(membership)
    assert "Model Org" in str(membership)
    assert str(event) == "Model Event"
    assert "member@example.com" in str(registration)
    assert "Model Event" in str(registration)
