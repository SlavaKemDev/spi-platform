from datetime import datetime

from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import *
from users.models import *

router = Router(tags=["Users"])


@router.get("upcoming")
def get_upcoming_events(request):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    events = Event.objects.filter(
        registration_start__lte=datetime.now(),
        registration_end__gte=datetime.now(),
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

    if event.registration_start > datetime.now() or event.registration_end < datetime.now():
        return {"error": "Registration for this event is not open"}

    if EventRegistration.objects.filter(user=user, event=event).exists():
        return {"error": "User is already registered for this event"}

    registration = EventRegistration.objects.create(user=user, event=event)

    return {
        "message": "User successfully registered for the event",
        "registration_id": registration.id
    }
