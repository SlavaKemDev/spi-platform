from django.http import Http404
from django.shortcuts import render


def auth_page(request):
    return render(request, 'auth.html')


def profile_page(request):
    # Auth check is done client-side via sessionStorage / /api/users/me.
    # To add server-side protection later: check request.user.is_authenticated here.
    return render(request, 'profile.html')
