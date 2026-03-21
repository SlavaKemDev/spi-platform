from django.utils import timezone

from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import *
from users.models import *
from organizations.models import *

router = Router(tags=["Organizations"])


@router.get("/my")
def get_my_organizations(request):
    user = request.user
    memberships = OrganizationMember.objects.filter(user=user)

    organizations = []

    for membership in memberships:
        organization = membership.organization

        organizations.append({
            "id": organization.id,
            "name": organization.name,
            "description": organization.description,
            "is_admin": membership.is_admin
        })

    return organizations


@router.get("/{organization_id}")
def get_organization_details(request, organization_id: int):
    user = request.user
    organization = get_object_or_404(Organization, id=organization_id)
    try:
        membership = OrganizationMember.objects.filter(organization=organization, user=user).first()
    except:
        membership = None

    if membership:
        events_set = organization.event_set.all()
    else:
        events_set = organization.event_set.filter(is_published=True)

    events = []

    for event in events_set:
        events.append({
            "id": event.id,
            "name": event.title,
            "description": event.description,

            "registration_start": event.registration_start,
            "registration_end": event.registration_end,

            "status": event.status,
            "is_published": event.is_published,

            "event_start": event.event_start,
            "event_end": event.event_end,
            "location": event.location,
            "format": event.format
        })

    return {
        "id": organization.id,
        "name": organization.name,
        "description": organization.description,
        "status": ("admin" if membership.is_admin else "member") if membership else "none",

        "events": events
    }
