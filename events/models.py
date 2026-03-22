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

    class FormType(models.TextChoices):
        SITE = 'site', 'Шаблон сайта'
        YANDEX = 'yandex', 'Яндекс Формы'
        GOOGLE = 'google', 'Google Формы'

    form_type = models.CharField(
        max_length=10,
        choices=FormType.choices,
        default=FormType.SITE,
        verbose_name='Тип формы регистрации',
    )
    form_url = models.URLField(blank=True, verbose_name='Ссылка на внешнюю форму')
    image = models.FileField(upload_to='event_images/', blank=True, null=True, verbose_name='Изображение')

    class Category(models.TextChoices):
        IT = 'it', 'IT'
        HACKATHON = 'hackathon', 'Хакатоны'
        STARTUP = 'startup', 'Стартапы'
        NETWORKING = 'networking', 'Нетворкинг'
        LECTURE = 'lecture', 'Лекции'
        MASTERCLASS = 'masterclass', 'Мастер-классы'
        GAMES = 'games', 'Игры'
        PARTY = 'party', 'Вечеринки'
        SPORT = 'sport', 'Спорт'
        SELF_DEV = 'self_dev', 'Саморазвитие'
        DATING = 'dating', 'Знакомства'

    categories = models.JSONField(default=list, blank=True, verbose_name='Категории')

    class AccessType(models.TextChoices):
        OPEN = 'open', 'Открытое'
        UNIVERSITY_ONLY = 'university_only', 'Только для студентов вуза организатора'
        CLOSED = 'closed', 'Закрытое'

    access_type = models.CharField(
        max_length=20,
        choices=AccessType.choices,
        default=AccessType.OPEN,
        verbose_name='Тип доступа',
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
    form_answer = models.JSONField(default=dict, blank=True, verbose_name='Ответы на форму регистрации')
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
