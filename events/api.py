from django.utils import timezone

from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import *
from users.models import *

router = Router(tags=["Events"])


@router.get("upcoming")
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
            "registration_start": event.registration_start,
            "registration_end": event.registration_end,
            "event_start": event.event_start,
            "event_end": event.event_end,
            "location": event.location,
            "format": event.format,
        })

    return events_list


@router.post("{event_id}/register")
def register_for_event(request, event_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    event: Event = get_object_or_404(Event, id=event_id)

    if event.registration_start > timezone.now() or event.registration_end < timezone.now():
        return {"error": "Registration for this event is not open"}

    if EventRegistration.objects.filter(user=user, event=event).exists():
        return {"error": "User is already registered for this event"}

    registration = EventRegistration.objects.create(user=user, event=event)

    return {
        "message": "User successfully registered for the event",
        "registration_id": registration.id
    }


@router.post("{event_id}/unregister")
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


@router.get("registrations")
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


@router.get("{event_id}")
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
        "registration_start": event.registration_start,
        "registration_end": event.registration_end,
        "event_start": event.event_start,
        "event_end": event.event_end,
        "location": event.location,
        "format": event.format,
        "my_registration": my_registration_dict
    }
