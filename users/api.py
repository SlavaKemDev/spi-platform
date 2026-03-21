from ninja import Router, Schema
from django.shortcuts import get_object_or_404

router = Router(tags=["Users"])


class UserRegistrationSchema(Schema):
    email: str
    password: str

    first_name: str
    last_name: str
    patronymic: str


@router.post("register")
def register(request, data: UserRegistrationSchema):
    return {"message": "User registered successfully"}


@router.get("me")
def get_current_user(request):
    return {"message": "Current user details"}
