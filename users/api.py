from django.utils import timezone
from datetime import datetime
from typing import Optional

from django.contrib.auth import login, logout
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from .models import *

router = Router(tags=["Users"])


def _detect_university(email: str):
    """Return University matching the email domain, using subdomain fallback."""
    domain = email.split('@')[-1].lower()
    # exact match first
    uni = University.objects.filter(email_domain__iexact=domain).first()
    if uni:
        return uni, True
    # subdomain match: e.g. user@edu.hse.ru matches hse.ru
    parts = domain.split('.')
    for i in range(1, len(parts) - 1):
        suffix = '.'.join(parts[i:])
        uni = University.objects.filter(email_domain__iexact=suffix).first()
        if uni:
            return uni, True
    return None, False


class UserRegistrationSchema(Schema):
    email: str
    password: str

    first_name: str
    last_name: str
    patronymic: str = ''

    birth_date: str = '2000-01-01'


class UserLoginSchema(Schema):
    email: str
    password: str


@router.post("register")
def register(request, data: UserRegistrationSchema):
    if User.objects.filter(email=data.email).exists():
        return {"error": "Email already exists"}

    # parse date
    try:
        birth_date = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
    except ValueError:
        return {"error": "Invalid birth date format. Use YYYY-MM-DD."}

    uni, confirmed = _detect_university(data.email)

    user = User.objects.create_user(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        birth_date=birth_date,
        university=uni,
        university_confirmed=confirmed,
    )

    login(request, user)

    return {
        "success": True,
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "email": user.email,
            "university_name": uni.name if uni else None,
            "university_confirmed": confirmed,
        }
    }


@router.post("login")
def login_view(request, data: UserLoginSchema):
    user = get_object_or_404(User, email=data.email)

    if not user.check_password(data.password):
        return {"error": "Invalid credentials"}

    login(request, user)

    return {
        "success": True,
        "message": "User logged in successfully",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }


@router.post("logout")
def logout_view(request):
    if not request.user.is_authenticated:
        return {"error": "User is not authenticated"}

    logout(request)

    return {"success": True, "message": "User logged out successfully"}


@router.get("me")
def get_current_user(request):
    if not request.user.is_authenticated:
        return {"error": "User is not authenticated"}

    user = request.user

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "patronymic": user.patronymic,
        "birth_date": user.birth_date.isoformat(),
        "university_id": user.university_id,
        "university_name": user.university.name if user.university else None,
        "university_confirmed": user.university_confirmed,
        "course": user.course,
    }


class UpdateUserSchema(Schema):
    first_name: str = ''
    last_name: str = ''
    patronymic: str = ''
    birth_date: str = ''
    course: Optional[int] = None
    university_id: Optional[int] = None


@router.post("me/update")
def update_current_user(request, data: UpdateUserSchema):
    if not request.user.is_authenticated:
        return {"error": "User is not authenticated"}

    user = request.user

    if data.first_name:
        user.first_name = data.first_name
    if data.last_name:
        user.last_name = data.last_name
    if data.patronymic is not None:
        user.patronymic = data.patronymic
    if data.birth_date:
        try:
            user.birth_date = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid birth date format. Use YYYY-MM-DD."}

    user.course = data.course

    # University: if provided manually, set but mark as not confirmed unless domain matches
    if data.university_id is not None:
        if data.university_id == 0:
            user.university = None
            user.university_confirmed = False
        else:
            uni = University.objects.filter(id=data.university_id).first()
            if uni:
                user.university = uni
                # re-check confirmation based on email
                detected_uni, _ = _detect_university(user.email)
                user.university_confirmed = (detected_uni is not None and detected_uni.id == uni.id)
    else:
        # Re-run auto-detection and update if found
        uni, confirmed = _detect_university(user.email)
        if uni and not user.university:
            user.university = uni
            user.university_confirmed = confirmed

    user.save()

    return {
        "success": True,
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "patronymic": user.patronymic,
        "university_id": user.university_id,
        "university_name": user.university.name if user.university else None,
        "university_confirmed": user.university_confirmed,
        "course": user.course,
    }


@router.get("universities")
def list_universities(request, q: str = ''):
    qs = University.objects.all()
    if q:
        qs = qs.filter(name__icontains=q)
    seen_names = set()
    result = []
    for u in qs[:50]:
        if u.name not in seen_names:
            seen_names.add(u.name)
            result.append({"id": u.id, "name": u.name, "email_domain": u.email_domain})
    return result


@router.get("universities/detect")
def detect_university(request):
    if not request.user.is_authenticated:
        return {"error": "User is not authenticated"}
    uni, confirmed = _detect_university(request.user.email)
    if uni:
        return {"id": uni.id, "name": uni.name, "confirmed": confirmed}
    return {"id": None, "name": None, "confirmed": False}
