from django.http import Http404
from django.shortcuts import render, redirect
from django.views.decorators.csrf import ensure_csrf_cookie


def user_profile(request):
    user = request.user
    if not user.is_authenticated:
        return Http404()

    context = {
        'email': user.email,
    }
    return render(request, 'home.html', context)


@ensure_csrf_cookie
def auth_page(request):
    if request.user.is_authenticated:
        return redirect('/profile/')
    return render(request, 'auth.html')


@ensure_csrf_cookie
def profile_page(request):
    if not request.user.is_authenticated:
        return redirect('/auth/')
    return render(request, 'profile.html')
