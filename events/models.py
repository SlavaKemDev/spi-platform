from django.db import models


class Event(models.Model):
    class Format(models.TextChoices):
        ONLINE = 'online', 'Онлайн'
        OFFLINE = 'offline', 'Оффлайн'

    title = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    date_start = models.DateTimeField(verbose_name='Дата начала')
    date_end = models.DateTimeField(verbose_name='Дата окончания')
    location = models.CharField(max_length=255, verbose_name='Место проведения')
    format = models.CharField(
        max_length=10,
        choices=Format.choices,
        verbose_name='Формат',
    )

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return self.title
