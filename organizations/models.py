from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    university = models.ForeignKey(
        'users.University', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Вуз организатора'
    )

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, verbose_name='Организация')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    is_admin = models.BooleanField(default=False, verbose_name='Администратор')

    class Meta:
        unique_together = ('organization', 'user')
        verbose_name = 'Участник организации'
        verbose_name_plural = 'Участники организации'

    def __str__(self):
        role = 'Администратор' if self.is_admin else 'Участник'
        return f'{self.user.email} - {self.organization.name} ({role})'
