from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date_start', 'date_end', 'location', 'format')
    list_filter = ('format',)
    search_fields = ('title', 'location')
    ordering = ('-date_start',)
