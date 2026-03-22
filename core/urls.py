"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.conf import settings
from django.conf.urls.static import static

from core.api import api
from users.views import auth_page, profile_page
from events.views import home, event_detail, organizer_page, about_page

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls),
    path('', home, name='home'),
    path('events/<int:event_id>/', event_detail, name='event_detail'),
    path('organizer/<int:event_id>/', organizer_page, name='organizer_page'),
    path('about/', about_page, name='about_page'),
    path('auth/', auth_page, name='auth'),
    path('profile/', profile_page, name='profile')
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
