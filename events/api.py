from django.utils import timezone
from datetime import datetime, timedelta
from typing import Optional

from django.shortcuts import get_object_or_404
from ninja import Router, Schema, File
from ninja.files import UploadedFile

from events.models import *
from organizations.models import OrganizationMember
from users.models import *

from .regform import validate_form_schema, validate_form_data
from .recommender import recommend as _knn_recommend

router = Router(tags=["Events"])


@router.get("/upcoming")
def get_upcoming_events(request):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    events = Event.objects.filter(
        registration_start__lte=timezone.now(),
        registration_end__gte=timezone.now(),
    ).select_related('organization')

    events_list = []
    for event in events:
        events_list.append({
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "registration_start": event.registration_start,
            "registration_end": event.registration_end,
            "event_start": event.event_start,
            "event_end": event.event_end,
            "location": event.location,
            "format": event.format,
            "categories": event.categories,
            "access_type": event.access_type,
            "organization_id": event.organization_id,
            "organization_name": event.organization.name,
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
    for registration in EventRegistration.objects.filter(event=event).select_related('user'):
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

    my_registration = EventRegistration.objects.filter(user=user, event=event).first()
    my_registration_dict = {
        "registered_at": my_registration.registered_at,
        "status": my_registration.status
    } if my_registration else None

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "form": event.form,
        "form_type": event.form_type,
        "form_url": event.form_url,
        "image_url": event.image.url if event.image else None,
        "status": event.status,
        "is_published": event.is_published,
        "registration_start": event.registration_start,
        "registration_end": event.registration_end,
        "event_start": event.event_start,
        "event_end": event.event_end,
        "location": event.location,
        "format": event.format,
        "organization_id": event.organization_id,
        "organization_name": event.organization.name,
        "categories": event.categories,
        "access_type": event.access_type,
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

    organization_member = get_object_or_404(OrganizationMember, user=user, organization_id=data.organization_id)

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

    form: list
    form_type: str = 'site'
    form_url: str = ''

    registration_start: str
    registration_end: str

    event_start: str
    event_end: str

    location: str
    format: str

    categories: list = []
    access_type: str = 'open'


@router.post("/{int:event_id}/update")
def update_draft_event(request, event_id: int, data: UpdateDraftEventSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    get_object_or_404(OrganizationMember, user=user, organization=event.organization)

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

    if data.form_type not in ('site', 'yandex', 'google'):
        return {"error": "Invalid form_type. Use 'site', 'yandex' or 'google'"}

    # Only validate form schema for site type
    if data.form_type == 'site':
        is_valid, err = validate_form_schema(data.form)
        if not is_valid:
            return {"error": f"Invalid form schema: {err}"}

    event.title = data.title
    event.description = data.description
    event.form = data.form if data.form_type == 'site' else []
    event.form_type = data.form_type
    event.form_url = data.form_url if data.form_type in ('yandex', 'google') else ''
    event.registration_start = registration_start
    event.registration_end = registration_end
    event.event_start = event_start
    event.event_end = event_end
    event.location = data.location
    event.format = data.format
    event.categories = data.categories
    event.access_type = data.access_type

    event.save()

    return {
        "message": "Draft event updated successfully",
        "event_id": event.id
    }


@router.post("/{int:event_id}/upload-image")
def upload_event_image(request, event_id: int, image: UploadedFile = File(...)):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    organization_member = OrganizationMember.objects.filter(user=user, organization=event.organization).first()
    if not organization_member:
        return {"error": "User is not a member of the event's organization"}

    # Delete old image if exists
    if event.image:
        event.image.delete(save=False)

    event.image.save(image.name, image, save=True)

    return {
        "success": True,
        "image_url": event.image.url,
    }


@router.post("/{int:event_id}/publish")
def publish_event(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    get_object_or_404(OrganizationMember, user=user, organization=event.organization)

    if event.is_published:
        return {"error": "Event is already published"}

    if not event.title:
        return {"error": "Event must have a title before publishing"}

    event.is_published = True
    event.save()

    return {
        "message": "Event published successfully",
        "event_id": event.id
    }


@router.get("/recommend")
def get_recommendation(request, exclude: str = "", interests: str = ""):
    """
    Returns the single best recommended event for the current user.
    exclude   — comma-separated event IDs to skip (session-excluded).
    interests — comma-separated category tags for onboarding preference.
    """
    exclude_ids = []
    if exclude:
        for part in exclude.split(','):
            part = part.strip()
            if part.isdigit():
                exclude_ids.append(int(part))

    interest_tags = [t.strip() for t in interests.split(',') if t.strip()] if interests else None

    ranked = _knn_recommend(request.user, exclude_ids=exclude_ids, interest_tags=interest_tags)
    if not ranked:
        return {"event": None}

    event, score = ranked[0]
    return {
        "event": {
            "id": event.id,
            "title": event.title,
            "description": event.description or '',
            "format": event.format,
            "location": event.location,
            "event_start": event.event_start,
            "registration_end": event.registration_end,
            "categories": event.categories,
            "access_type": event.access_type,
            "image_url": event.image.url if event.image else None,
            "organization_name": event.organization.name,
            "organization_id": event.organization_id,
        }
    }
