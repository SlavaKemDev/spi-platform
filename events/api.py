from datetime import date, datetime

from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import Event
from users.models import User

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
