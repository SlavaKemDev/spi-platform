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
        "birth_date": user.birth_date.isoformat(),
    }
