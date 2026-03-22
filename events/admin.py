from django.contrib import admin

from .models import Event, EventRegistration, EventTag


@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = ('registered_at',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'registration_start', 'registration_end', 'event_start', 'event_end', 'location', 'format')
    list_filter = ('format', 'tags')
    search_fields = ('title', 'location')
    ordering = ('-event_start',)
    filter_horizontal = ('tags',)
    inlines = (EventRegistrationInline,)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'registered_at')
    list_filter = ('status', 'event')
    search_fields = ('user__email', 'event__title')
    readonly_fields = ('registered_at',)
