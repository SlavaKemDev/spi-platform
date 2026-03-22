from django.contrib import admin

from .models import Event, EventRegistration, EventTag, ExternalForm


@admin.register(EventTag)
class EventTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = ('registered_at',)


class ExternalFormInline(admin.StackedInline):
    model = ExternalForm
    extra = 0
    readonly_fields = ('parsed_form', 'field_mapping')
    fields = ('parsed_form', 'field_mapping')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_external', 'is_published', 'registration_start', 'registration_end', 'event_start', 'event_end', 'location', 'format')
    list_filter = ('format', 'is_external', 'is_published', 'tags')
    search_fields = ('title', 'location')
    ordering = ('-event_start',)
    filter_horizontal = ('tags',)
    inlines = (ExternalFormInline, EventRegistrationInline)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'registered_at')
    list_filter = ('status', 'event')
    search_fields = ('user__email', 'event__title')
    readonly_fields = ('registered_at',)


@admin.register(ExternalForm)
class ExternalFormAdmin(admin.ModelAdmin):
    list_display = ('event', 'form_url', 'has_mapping')
    search_fields = ('event__title',)
    readonly_fields = ('parsed_form', 'field_mapping')
    fields = ('event', 'parsed_form', 'field_mapping')

    def form_url(self, obj):
        return obj.parsed_form.get('url', '—')
    form_url.short_description = 'URL формы'

    def has_mapping(self, obj):
        return bool(obj.field_mapping)
    has_mapping.boolean = True
    has_mapping.short_description = 'Маппинг готов'
