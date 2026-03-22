from django.utils import timezone
from datetime import datetime

from django.contrib.auth import login, logout
from ninja import Router, Schema
from django.shortcuts import get_object_or_404
from .models import *

router = Router(tags=["Users"])


class UserRegistrationSchema(Schema):
    email: str
    password: str

    first_name: str
    last_name: str
    patronymic: str

    birth_date: str


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

    user = User.objects.create_user(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        birth_date=birth_date,
    )

    login(request, user)

    return {
        "success": True,
        "message": "User registered successfully",
        "user": {
            "id": user.id,
            "email": user.email
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
        "birth_date": user.birth_date.isoformat() if user.birth_date else "",
        "university": user.university.name if user.university else "",
        "faculty": user.faculty or "",
        "course": user.course or "",
    }


class UpdateProfileSchema(Schema):
    first_name: str = ""
    last_name: str = ""
    patronymic: str = ""
    birth_date: str = ""
    university: str = ""
    faculty: str = ""
    course: str = ""


@router.post("me/update")
def update_current_user(request, data: UpdateProfileSchema):
    if not request.user.is_authenticated:
        return {"error": "User is not authenticated"}

    user = request.user

    if data.first_name:
        user.first_name = data.first_name
    if data.last_name:
        user.last_name = data.last_name
    if data.patronymic is not None:
        user.patronymic = data.patronymic
    if data.faculty is not None:
        user.faculty = data.faculty
    if data.course is not None:
        user.course = data.course

    if data.birth_date:
        try:
            user.birth_date = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "Invalid birth date format. Use YYYY-MM-DD."}

    if data.university is not None:
        if data.university.strip():
            uni, _ = University.objects.get_or_create(name=data.university.strip(), defaults={"email_domain": ""})
            user.university = uni
        else:
            user.university = None

    user.save()

    return {"success": True, "message": "Profile updated successfully"}
