from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    email = models.EmailField(_('email address'), blank=True, null=True)
    phone = models.CharField(_('Phone number'), max_length=20, blank=True)
    address = models.TextField(_('Address'), blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
        ]


    def __str__(self):
        return self.get_full_name() or self.username

    def full_name(self):
        return self.get_full_name()

    def is_admin(self):
        return self.is_staff or self.is_superuser