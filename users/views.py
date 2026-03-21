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
