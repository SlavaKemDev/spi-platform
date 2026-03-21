from django.http import Http404
from django.shortcuts import render


def user_profile(request):
    user = request.user
    if not user.is_authenticated:
        return Http404()

    context = {
        'email': user.email,
    }
    return render(request, 'home.html', context)


def auth_page(request):
    return render(request, 'auth.html')


def profile_page(request):
    # Auth check is done client-side via sessionStorage / /api/users/me.
    # To add server-side protection later: check request.user.is_authenticated here.
    return render(request, 'profile.html')
