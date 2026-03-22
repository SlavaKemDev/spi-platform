from django.utils import timezone
from datetime import datetime, timedelta
from typing import Optional

from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import *
from organizations.models import OrganizationMember
from users.models import *

from .regform import validate_form_schema, validate_form_data
from forms_wrapper.form_reader import read_form
from forms_wrapper.field_matcher import match_fields, apply_mapping

router = Router(tags=["Events"])


@router.get("/upcoming")
def get_upcoming_events(request):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    events = Event.objects.filter(
        registration_start__lte=timezone.now(),
        registration_end__gte=timezone.now(),
    )

    events_list = []
    for event in events:
        events_list.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "image": event.image.url if event.image else None,
            "registration_start": event.registration_start,
            "registration_end": event.registration_end,
            "event_start": event.event_start,
            "event_end": event.event_end,
            "location": event.location,
            "format": event.format,
        })

    return events_list


class EventRegistrationSchema(Schema):
    form_answer: dict


@router.post("/{int:event_id}/register")
def register_for_event(request, event_id: int, data: EventRegistrationSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    if event.is_external:
        return {"error": "This event uses an external registration form. Use /registration-link to get a prefilled URL."}

    if event.registration_start > timezone.now() or event.registration_end < timezone.now():
        return {"error": "Registration for this event is not open"}

    if EventRegistration.objects.filter(user=user, event=event).exists():
        return {"error": "User is already registered for this event"}

    is_valid, err = validate_form_data(data.form_answer, event.form)

    if not is_valid:
        return {"error": f"Invalid form answer: {err}"}

    registration = EventRegistration.objects.create(user=user, event=event, form_answer=data.form_answer)

    return {
        "message": "User successfully registered for the event",
        "registration_id": registration.id
    }


@router.post("/{int:event_id}/unregister")
def unregister_from_event(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    registration = EventRegistration.objects.filter(user=user, event=event).first()
    if not registration:
        return {"error": "User is not registered for this event"}

    registration.delete()

    return {"message": "User successfully unregistered from the event"}


@router.get("/registrations")
def get_user_registrations(request):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    registration_list = []
    for registration in EventRegistration.objects.filter(user=user):
        registration_list.append({
            "id": registration.event.id,
            "title": registration.event.title,
            "registered_at": registration.registered_at,
            "status": registration.status
        })

    return registration_list


@router.get("/{int:event_id}/registrations")
def get_event_registrations(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    organization_member = OrganizationMember.objects.filter(user=user, organization=event.organization).first()
    if not organization_member:
        return {"error": "User is not a member of the event's organization"}

    registration_list = []
    for registration in EventRegistration.objects.filter(event=event):
        registration_list.append({
            "id": registration.id,
            "user_email": registration.user.email,
            "user_first_name": registration.user.first_name,
            "user_last_name": registration.user.last_name,
            "registered_at": registration.registered_at,
            "status": registration.status,
            "form_answer": registration.form_answer,
        })

    return registration_list


@router.get("/{int:event_id}")
def get_event_details(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    if EventRegistration.objects.filter(user=user, event=event).exists():
        my_registration = EventRegistration.objects.get(user=user, event=event)
        my_registration_dict = {
            "registered_at": my_registration.registered_at,
            "status": my_registration.status
        }
    else:
        my_registration_dict = None

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "image": event.image.url if event.image else None,
        "is_external": event.is_external,
        "form": None if event.is_external else event.form,
        "registration_start": event.registration_start,
        "registration_end": event.registration_end,
        "event_start": event.event_start,
        "event_end": event.event_end,
        "location": event.location,
        "format": event.format,
        "my_registration": my_registration_dict
    }


class ReviewRegistrationSchema(Schema):
    status: str  # "approved" or "rejected"


@router.post("/registrations/{int:registration_id}/review")
def review_registration(request, registration_id: int, data: ReviewRegistrationSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    if data.status not in (EventRegistration.Status.APPROVED, EventRegistration.Status.REJECTED):
        return {"error": "Invalid status. Use 'approved' or 'rejected'"}

    registration: EventRegistration = get_object_or_404(EventRegistration, id=registration_id)

    organization_member = OrganizationMember.objects.filter(user=user, organization=registration.event.organization).first()
    if not organization_member:
        return {"error": "User is not a member of the event's organization"}


    registration.status = data.status
    registration.save()

    return {
        "message": "Registration status updated successfully",
        "registration_id": registration.id,
        "status": registration.status
    }



class CreateDraftEventSchema(Schema):
    organization_id: int


@router.post("/create")
def create_draft_event(request, data: CreateDraftEventSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization_member = OrganizationMember.objects.filter(user=user, organization_id=data.organization_id).first()
    if not organization_member:
        return {"error": "User is not a member of this organization"}

    organization = organization_member.organization

    event = Event.objects.create(
        title="",
        description="",
        organization=organization,
        registration_start=timezone.now(),
        registration_end=timezone.now() + timedelta(days=7),
        event_start=timezone.now() + timedelta(days=14),
        event_end=timezone.now() + timedelta(days=15),
        location="",
        format=Event.Format.OFFLINE,
    )

    return {
        "message": "Draft event created successfully",
        "event_id": event.id
    }


class UpdateDraftEventSchema(Schema):
    title: str
    description: str

    form: Optional[list] = None

    registration_start: str
    registration_end: str

    event_start: str
    event_end: str

    location: str

    format: str


@router.post("/{int:event_id}/update")
def update_draft_event(request, event_id: int, data: UpdateDraftEventSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    organization_member = OrganizationMember.objects.filter(user=user, organization=event.organization).first()
    if not organization_member:
        return {"error": "User is not a member of the event's organization"}

    if event.is_published:
        return {"error": "Cannot update a published event"}

    # parse dates
    try:
        registration_start = timezone.make_aware(datetime.strptime(data.registration_start, "%Y-%m-%dT%H:%M:%S"))
        registration_end = timezone.make_aware(datetime.strptime(data.registration_end, "%Y-%m-%dT%H:%M:%S"))
        event_start = timezone.make_aware(datetime.strptime(data.event_start, "%Y-%m-%dT%H:%M:%S"))
        event_end = timezone.make_aware(datetime.strptime(data.event_end, "%Y-%m-%dT%H:%M:%S"))
    except ValueError:
        return {"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS."}

    if registration_start >= registration_end:
        return {"error": "Registration start date must be before registration end date"}
    if registration_end > event_start:
        return {"error": "Registration end date must be before event start date"}
    if event_start >= event_end:
        return {"error": "Event start date must be before event end date"}

    if not event.is_external:
        form = data.form or []
        is_valid, err = validate_form_schema(form)
        if not is_valid:
            return {"error": f"Invalid form schema: {err}"}
        event.form = form

    event.title = data.title
    event.description = data.description
    event.registration_start = registration_start
    event.registration_end = registration_end
    event.event_start = event_start
    event.event_end = event_end
    event.location = data.location
    event.format = data.format

    event.save()

    return {
        "message": "Draft event updated successfully",
        "event_id": event.id
    }


class AttachExternalFormSchema(Schema):
    url: str


@router.post("/{int:event_id}/attach-external-form")
def attach_external_form(request, event_id: int, data: AttachExternalFormSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    if event.is_published:
        return {"error": "Cannot attach external form to a published event"}

    organization_member = OrganizationMember.objects.filter(user=user, organization=event.organization).first()
    if not organization_member:
        return {"error": "User is not a member of the event's organization"}

    try:
        parsed = read_form(data.url)
    except Exception as e:
        return {"error": f"Failed to parse form: {e}"}

    db_columns = ["email", "first_name", "last_name", "patronymic", "birth_date"]

    try:
        result = match_fields(parsed, db_columns)
    except Exception as e:
        return {"error": f"Failed to match fields: {e}"}

    ExternalForm.objects.update_or_create(
        event=event,
        defaults={
            "parsed_form": parsed,
            "field_mapping": result["mapping"],
        }
    )

    event.is_external = True
    event.save()

    return {
        "message": "External form attached successfully",
        "manual_fields": result["manual_fields"],
    }


@router.get("/{int:event_id}/registration-link")
def get_registration_link(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    if not event.is_external:
        return {"error": "This event does not use an external form"}

    if not event.is_published:
        return {"error": "Event is not published"}

    if event.registration_start > timezone.now() or event.registration_end < timezone.now():
        return {"error": "Registration for this event is not open"}

    try:
        external_form = event.external_form
    except ExternalForm.DoesNotExist:
        return {"error": "External form is not configured for this event"}

    user_profile = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "patronymic": user.patronymic,
        "birth_date": str(user.birth_date),
    }

    result = apply_mapping(external_form.parsed_form, external_form.field_mapping, user_profile)

    return {
        "prefill_url": result["prefill_url"],
        "manual_fields": result["manual_fields"],
    }


@router.post("/{int:event_id}/publish")
def publish_event(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    organization_member = OrganizationMember.objects.filter(user=user, organization=event.organization).first()
    if not organization_member:
        return {"error": "User is not a member of the event's organization"}

    if event.is_published:
        return {"error": "Event is already published"}

    if event.is_external and not ExternalForm.objects.filter(event=event).exists():
        return {"error": "Cannot publish: external form is not attached"}

    event.is_published = True
    event.save()

    return {
        "message": "Event published successfully",
        "event_id": event.id
    }


