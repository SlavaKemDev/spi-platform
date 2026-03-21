from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'registration_start', 'registration_end', 'event_start', 'event_end', 'location', 'format')
    list_filter = ('format',)
    search_fields = ('title', 'location')
    ordering = ('-event_start',)
