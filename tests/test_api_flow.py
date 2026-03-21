from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from events.models import Event, EventRegistration
from organizations.models import Organization, OrganizationMember


pytestmark = pytest.mark.django_db


def test_full_organization_event_flow_via_orm_and_api(register_and_login, api_post, api_datetime):
    organization = Organization.objects.create(
        name="Engineering Club",
        description="Student organization for project events",
    )

    admin_client = Client()
    participant_client = Client()

    admin_user, admin_payload = register_and_login(admin_client, prefix="admin")
    participant_user, participant_payload = register_and_login(participant_client, prefix="participant")

    admin_me = admin_client.get("/api/users/me")
    assert admin_me.status_code == 200
    assert admin_me.json()["email"] == admin_payload["email"]

    participant_me = participant_client.get("/api/users/me")
    assert participant_me.status_code == 200
    assert participant_me.json()["email"] == participant_payload["email"]

    OrganizationMember.objects.create(
        organization=organization,
        user=admin_user,
        is_admin=True,
    )

    admin_organizations = admin_client.get("/api/organizations/my")
    assert admin_organizations.status_code == 200
    assert admin_organizations.json() == [
        {
            "id": organization.id,
            "name": organization.name,
            "description": organization.description,
            "is_admin": True,
        }
    ]

    participant_organizations = participant_client.get("/api/organizations/my")
    assert participant_organizations.status_code == 200
    assert participant_organizations.json() == []

    admin_org_details = admin_client.get(f"/api/organizations/{organization.id}")
    assert admin_org_details.status_code == 200
    assert admin_org_details.json()["status"] == "admin"
    assert admin_org_details.json()["events"] == []

    participant_org_details = participant_client.get(f"/api/organizations/{organization.id}")
    assert participant_org_details.status_code == 200
    assert participant_org_details.json()["status"] == "none"
    assert participant_org_details.json()["events"] == []

    create_event_response = api_post(
        admin_client,
        "/api/events/create",
        {"organization_id": organization.id},
    )
    assert create_event_response.status_code == 200
    create_event_body = create_event_response.json()
    assert create_event_body["message"] == "Draft event created successfully"

    event = Event.objects.get(id=create_event_body["event_id"])
    assert event.organization_id == organization.id
    assert event.is_published is False

    admin_org_after_create = admin_client.get(f"/api/organizations/{organization.id}")
    assert admin_org_after_create.status_code == 200
    admin_events = admin_org_after_create.json()["events"]
    assert len(admin_events) == 1
    assert admin_events[0]["id"] == event.id
    assert admin_events[0]["is_published"] is False

    participant_org_after_create = participant_client.get(f"/api/organizations/{organization.id}")
    assert participant_org_after_create.status_code == 200
    assert participant_org_after_create.json()["events"] == []

    now = timezone.now().replace(microsecond=0)
    form_definition = [
        {
            "name": "motivation",
            "label": "Motivation",
            "type": "textarea",
            "required": True,
        },
        {
            "name": "track",
            "label": "Track",
            "type": "select",
            "required": True,
            "options": ["AI", "Web"],
        },
        {
            "name": "experience",
            "label": "Experience",
            "type": "number",
            "required": False,
        },
        {
            "name": "newsletter",
            "label": "Newsletter",
            "type": "checkbox",
            "required": False,
        },
    ]
    update_payload = {
        "title": "Spring Hackathon",
        "description": "48-hour event for student teams",
        "form": form_definition,
        "registration_start": api_datetime(now - timedelta(days=1)),
        "registration_end": api_datetime(now + timedelta(days=1)),
        "event_start": api_datetime(now + timedelta(days=2)),
        "event_end": api_datetime(now + timedelta(days=3)),
        "location": "Main Campus",
        "format": Event.Format.ONLINE,
    }

    update_event_response = api_post(
        admin_client,
        f"/api/events/{event.id}/update",
        update_payload,
    )
    assert update_event_response.status_code == 200
    assert update_event_response.json()["message"] == "Draft event updated successfully"

    event.refresh_from_db()
    assert event.title == update_payload["title"]
    assert event.description == update_payload["description"]
    assert event.form == form_definition
    assert event.location == update_payload["location"]
    assert event.format == update_payload["format"]

    publish_response = admin_client.post(f"/api/events/{event.id}/publish")
    assert publish_response.status_code == 200
    assert publish_response.json()["message"] == "Event published successfully"

    event.refresh_from_db()
    assert event.is_published is True

    participant_org_after_publish = participant_client.get(f"/api/organizations/{organization.id}")
    assert participant_org_after_publish.status_code == 200
    published_events = participant_org_after_publish.json()["events"]
    assert len(published_events) == 1
    assert published_events[0]["id"] == event.id
    assert published_events[0]["name"] == update_payload["title"]

    upcoming_response = participant_client.get("/api/events/upcoming")
    assert upcoming_response.status_code == 200
    upcoming_event_ids = {item["id"] for item in upcoming_response.json()}
    assert event.id in upcoming_event_ids

    event_details_before_registration = participant_client.get(f"/api/events/{event.id}")
    assert event_details_before_registration.status_code == 200
    event_details_body = event_details_before_registration.json()
    assert event_details_body["title"] == update_payload["title"]
    assert event_details_body["form"] == form_definition
    assert event_details_body["my_registration"] is None

    invalid_registration_response = api_post(
        participant_client,
        f"/api/events/{event.id}/register",
        {"form_answer": {"track": "AI"}},
    )
    assert invalid_registration_response.status_code == 200
    assert "Motivation" in invalid_registration_response.json()["error"]

    register_response = api_post(
        participant_client,
        f"/api/events/{event.id}/register",
        {
            "form_answer": {
                "motivation": "I want to build a project",
                "track": "AI",
                "experience": 2,
                "newsletter": True,
            }
        },
    )
    assert register_response.status_code == 200
    assert register_response.json()["message"] == "User successfully registered for the event"

    registration = EventRegistration.objects.get(event=event, user=participant_user)

    duplicate_register_response = api_post(
        participant_client,
        f"/api/events/{event.id}/register",
        {"form_answer": {"motivation": "Duplicate", "track": "AI"}},
    )
    assert duplicate_register_response.status_code == 200
    assert duplicate_register_response.json()["error"] == "User is already registered for this event"

    registrations_response = participant_client.get("/api/events/registrations")
    assert registrations_response.status_code == 200
    registrations_body = registrations_response.json()
    assert len(registrations_body) == 1
    assert registrations_body[0]["id"] == event.id
    assert registrations_body[0]["status"] == EventRegistration.Status.PENDING

    event_details_after_registration = participant_client.get(f"/api/events/{event.id}")
    assert event_details_after_registration.status_code == 200
    assert event_details_after_registration.json()["my_registration"]["status"] == EventRegistration.Status.PENDING

    forbidden_review_response = api_post(
        participant_client,
        f"/api/events/registrations/{registration.id}/review",
        {"status": EventRegistration.Status.APPROVED},
    )
    assert forbidden_review_response.status_code == 200
    assert forbidden_review_response.json()["error"] == "User is not a member of the event's organization"

    invalid_review_response = api_post(
        admin_client,
        f"/api/events/registrations/{registration.id}/review",
        {"status": "unknown"},
    )
    assert invalid_review_response.status_code == 200
    assert invalid_review_response.json()["error"] == "Invalid status. Use 'approved' or 'rejected'"

    approve_response = api_post(
        admin_client,
        f"/api/events/registrations/{registration.id}/review",
        {"status": EventRegistration.Status.APPROVED},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == EventRegistration.Status.APPROVED

    registration.refresh_from_db()
    assert registration.status == EventRegistration.Status.APPROVED

    registrations_after_review = participant_client.get("/api/events/registrations")
    assert registrations_after_review.status_code == 200
    assert registrations_after_review.json()[0]["status"] == EventRegistration.Status.APPROVED

    unregister_response = participant_client.post(f"/api/events/{event.id}/unregister")
    assert unregister_response.status_code == 200
    assert unregister_response.json()["message"] == "User successfully unregistered from the event"

    assert not EventRegistration.objects.filter(event=event, user=participant_user).exists()

    duplicate_unregister_response = participant_client.post(f"/api/events/{event.id}/unregister")
    assert duplicate_unregister_response.status_code == 200
    assert duplicate_unregister_response.json()["error"] == "User is not registered for this event"

    registrations_after_unregister = participant_client.get("/api/events/registrations")
    assert registrations_after_unregister.status_code == 200
    assert registrations_after_unregister.json() == []

    event_details_after_unregister = participant_client.get(f"/api/events/{event.id}")
    assert event_details_after_unregister.status_code == 200
    assert event_details_after_unregister.json()["my_registration"] is None

    home_response = participant_client.get("/home")
    assert home_response.status_code == 200
    assert participant_payload["email"] in home_response.content.decode()


def test_user_api_validation_and_auth_checks(api_post, user_payload_factory):
    anonymous_client = Client()

    me_response = anonymous_client.get("/api/users/me")
    assert me_response.status_code == 200
    assert me_response.json()["error"] == "User is not authenticated"

    upcoming_response = anonymous_client.get("/api/events/upcoming")
    assert upcoming_response.status_code == 200
    assert upcoming_response.json()["error"] == "User is not authenticated"

    invalid_birth_date_payload = user_payload_factory(prefix="invalid-date")
    invalid_birth_date_payload["birth_date"] = "01-01-2000"
    invalid_birth_date_response = api_post(
        anonymous_client,
        "/api/users/register",
        invalid_birth_date_payload,
    )
    assert invalid_birth_date_response.status_code == 200
    assert invalid_birth_date_response.json()["error"] == "Invalid birth date format. Use YYYY-MM-DD."

    valid_payload = user_payload_factory(prefix="duplicate-check")
    first_register_response = api_post(anonymous_client, "/api/users/register", valid_payload)
    assert first_register_response.status_code == 200
    assert first_register_response.json()["success"] is True

    duplicate_register_response = api_post(anonymous_client, "/api/users/register", valid_payload)
    assert duplicate_register_response.status_code == 200
    assert duplicate_register_response.json()["error"] == "Email already exists"

    anonymous_client.logout()

    invalid_login_response = api_post(
        anonymous_client,
        "/api/users/login",
        {"email": valid_payload["email"], "password": "wrong-password"},
    )
    assert invalid_login_response.status_code == 200
    assert invalid_login_response.json()["error"] == "Invalid credentials"
