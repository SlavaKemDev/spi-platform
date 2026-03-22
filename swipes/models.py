from django.db import models


class EventSwipe(models.Model):
    class Status(models.TextChoices):
        LIKE = 'like', 'Лайк'
        DISLIKE = 'dislike', 'Дизлайк'
        PENDING = 'pending', 'Ожидание'

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, verbose_name='Пользователь')
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, verbose_name='Событие')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус',
    )

    def __str__(self):
        return f"{self.user.email} - {self.event.title} ({self.status})"

    class Meta:
        verbose_name = 'Свайп события'
        verbose_name_plural = 'Свайпы событий'
        unique_together = ('user', 'event')
