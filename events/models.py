from django.db import models
from django.utils import timezone


class Event(models.Model):
    class Format(models.TextChoices):
        ONLINE = 'online', 'Онлайн'
        OFFLINE = 'offline', 'Оффлайн'

    title = models.CharField(max_length=255, verbose_name='Название', blank=True)
    description = models.TextField(verbose_name='Описание', blank=True)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE, verbose_name='Организация')

    is_published = models.BooleanField(default=False, verbose_name='Опубликовано')

    form = models.JSONField(default=list, blank=True, verbose_name='Поля формы регистрации')

    registration_start = models.DateTimeField(verbose_name='Дата начала регистрации')
    registration_end = models.DateTimeField(verbose_name='Дата окончания регистрации')

    event_start = models.DateTimeField(verbose_name='Дата начала')
    event_end = models.DateTimeField(verbose_name='Дата окончания')

    location = models.CharField(max_length=255, verbose_name='Место проведения', blank=True)
    format = models.CharField(
        max_length=10,
        choices=Format.choices,
        verbose_name='Формат',
    )

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    @property
    def status(self):
        if timezone.now() < self.registration_start:
            return "upcoming"
        elif timezone.now() <= self.registration_end:
            return "registration_open"
        elif timezone.now() < self.event_start:
            return "registration_closed"
        elif timezone.now() <= self.event_end:
            return "ongoing"
        else:
            return "past"

    def __str__(self):
        return self.title


class EventRegistration(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Не рассмотрено'
        APPROVED = 'approved', 'Одобрено'
        REJECTED = 'rejected', 'Отклонено'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name='Событие')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус',
    )

    def __str__(self):
        return f"{self.user.email} - {self.event.title}"

    class Meta:
        verbose_name = 'Регистрация на событие'
        verbose_name_plural = 'Регистрации на события'
        unique_together = ('event', 'user')
