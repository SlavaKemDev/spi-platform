from django.utils import timezone

from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from events.models import *
from users.models import *
from organizations.models import *

router = Router(tags=["Organizations"])


@router.get("/")
def get_all_organizations(request):
    organizations = []
    for organization in Organization.objects.all():
        organizations.append({
            "id": organization.id,
            "name": organization.name,
            "description": organization.description,
        })
    return organizations


@router.get("/my")
def get_my_organizations(request):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

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


class CreateOrganizationSchema(Schema):
    name: str
    description: str = ""


@router.post("/create")
def create_organization(request, data: CreateOrganizationSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = Organization.objects.create(
        name=data.name,
        description=data.description,
    )
    OrganizationMember.objects.create(
        organization=organization,
        user=user,
        is_admin=True,
    )

    return {
        "success": True,
        "id": organization.id,
        "name": organization.name,
        "description": organization.description,
    }


class UpdateOrganizationSchema(Schema):
    name: str
    description: str = ""


@router.post("/{int:organization_id}/update")
def update_organization(request, organization_id: int, data: UpdateOrganizationSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = get_object_or_404(Organization, id=organization_id)

    requester = OrganizationMember.objects.filter(user=user, organization=organization).first()
    if not requester or not requester.is_admin:
        return {"error": "User is not an admin of this organization"}

    organization.name = data.name
    organization.description = data.description
    organization.save()

    return {"success": True, "id": organization.id, "name": organization.name}


class AddMemberSchema(Schema):
    user_id: int


@router.post("/{int:organization_id}/members/add")
def add_member(request, organization_id: int, data: AddMemberSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = get_object_or_404(Organization, id=organization_id)

    requester = OrganizationMember.objects.filter(user=user, organization=organization).first()
    if not requester or not requester.is_admin:
        return {"error": "User is not an admin of this organization"}

    target_user = get_object_or_404(User, id=data.user_id)

    if OrganizationMember.objects.filter(user=target_user, organization=organization).exists():
        return {"error": "User is already a member of this organization"}

    OrganizationMember.objects.create(user=target_user, organization=organization, is_admin=False)

    return {"success": True, "message": "User added to organization"}


@router.post("/{int:organization_id}/members/{int:user_id}/promote")
def promote_to_admin(request, organization_id: int, user_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = get_object_or_404(Organization, id=organization_id)

    requester = OrganizationMember.objects.filter(user=user, organization=organization).first()
    if not requester or not requester.is_admin:
        return {"error": "User is not an admin of this organization"}

    member = OrganizationMember.objects.filter(user_id=user_id, organization=organization).first()
    if not member:
        return {"error": "User is not a member of this organization"}

    if member.is_admin:
        return {"error": "User is already an admin"}

    member.is_admin = True
    member.save()

    return {"success": True, "message": "User promoted to admin"}


@router.get("/{int:organization_id}/members")
def get_organization_members(request, organization_id: int):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = get_object_or_404(Organization, id=organization_id)

    requester = OrganizationMember.objects.filter(user=user, organization=organization).first()
    if not requester:
        return {"error": "Access denied"}

    members = []
    for m in OrganizationMember.objects.filter(organization=organization).select_related('user'):
        members.append({
            "user_id": m.user.id,
            "email": m.user.email,
            "first_name": m.user.first_name,
            "last_name": m.user.last_name,
            "patronymic": m.user.patronymic,
            "is_admin": m.is_admin,
        })
    return members


class RemoveMemberSchema(Schema):
    user_id: int


@router.post("/{int:organization_id}/members/remove")
def remove_member(request, organization_id: int, data: RemoveMemberSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = get_object_or_404(Organization, id=organization_id)

    requester = OrganizationMember.objects.filter(user=user, organization=organization).first()
    if not requester or not requester.is_admin:
        return {"error": "User is not an admin of this organization"}

    if data.user_id == user.id:
        return {"error": "Cannot remove yourself"}

    member = OrganizationMember.objects.filter(user_id=data.user_id, organization=organization).first()
    if not member:
        return {"error": "User is not a member of this organization"}

    member.delete()
    return {"success": True}


class AddMemberByEmailSchema(Schema):
    email: str


@router.post("/{int:organization_id}/members/add-by-email")
def add_member_by_email(request, organization_id: int, data: AddMemberByEmailSchema):
    user = request.user
    if not user.is_authenticated:
        return {"error": "User is not authenticated"}

    organization = get_object_or_404(Organization, id=organization_id)

    requester = OrganizationMember.objects.filter(user=user, organization=organization).first()
    if not requester or not requester.is_admin:
        return {"error": "User is not an admin of this organization"}

    target_user = User.objects.filter(email__iexact=data.email.strip()).first()
    if not target_user:
        return {"error": "Пользователь с таким email не найден"}

    if OrganizationMember.objects.filter(user=target_user, organization=organization).exists():
        return {"error": "Пользователь уже является участником организации"}

    OrganizationMember.objects.create(user=target_user, organization=organization, is_admin=False)
    return {
        "success": True,
        "user_id": target_user.id,
        "email": target_user.email,
        "first_name": target_user.first_name,
        "last_name": target_user.last_name,
        "is_admin": False,
    }


@router.get("/{organization_id}")
def get_organization_details(request, organization_id: int):
    user = request.user
    organization = get_object_or_404(Organization, id=organization_id)
    try:
        membership = OrganizationMember.objects.filter(organization=organization, user=user).first()
    except Exception:
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
            "format": event.format,
            "form_type": event.form_type,
        })

    return {
        "id": organization.id,
        "name": organization.name,
        "description": organization.description,
        "status": ("admin" if membership.is_admin else "member") if membership else "none",

        "events": events
    }
