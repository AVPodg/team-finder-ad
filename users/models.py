# users/models.py
from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from users.constants import (
    USER_ABOUT_MAX_LENGTH,
    USER_NAME_MAX_LENGTH,
    USER_PHONE_MAX_LENGTH,
    USER_SURNAME_MAX_LENGTH,
)
from users.services import avatar_upload_to, build_avatar
from users.validators import normalize_phone, validate_github_url
from users.managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=USER_NAME_MAX_LENGTH)
    surname = models.CharField(max_length=USER_SURNAME_MAX_LENGTH)
    avatar = models.ImageField(upload_to=avatar_upload_to)
    phone = models.CharField(max_length=USER_PHONE_MAX_LENGTH, unique=True)
    github_url = models.URLField(blank=True, validators=[validate_github_url])
    about = models.CharField(max_length=USER_ABOUT_MAX_LENGTH, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    favorites = models.ManyToManyField(
        "projects.Project",
        blank=True,
        related_name="interested_users"
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname", "phone"]

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return f"{self.name} {self.surname}".strip() or self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
        self.phone = normalize_phone(self.phone)
        validate_github_url(self.github_url)

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.save(
                f"{self.email.split('@')[0]}_avatar.png",
                build_avatar(self.name),
                save=False,
            )
        self.full_clean()
        super().save(*args, **kwargs)