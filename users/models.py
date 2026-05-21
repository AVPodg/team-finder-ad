from __future__ import annotations

import hashlib
import re
from io import BytesIO
from urllib.parse import urlparse

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont


PHONE_RE = re.compile(r"^\+7\d{10}$")


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits.startswith("8"):
        digits = f"7{digits[1:]}"
    if len(digits) == 11 and digits.startswith("7"):
        normalized = f"+{digits}"
        if PHONE_RE.match(normalized):
            return normalized
    raise ValidationError("Введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX.")


def validate_github_url(value: str) -> None:
    if not value:
        return
    parsed = urlparse(value)
    hostname = (parsed.hostname or "").lower()
    if hostname not in {"github.com", "www.github.com"}:
        raise ValidationError("Укажите ссылку на github.com.")


def avatar_upload_to(instance: "User", filename: str) -> str:
    return f"avatars/user_{instance.pk or 'new'}.png"


def build_avatar(first_letter: str) -> ContentFile:
    size = 256
    letter = (first_letter or "?").strip()[:1].upper() or "?"
    palette = [
        "#2563EB",
        "#7C3AED",
        "#DB2777",
        "#EA580C",
        "#16A34A",
        "#0891B2",
    ]
    color = palette[int(hashlib.md5(letter.encode(), usedforsecurity=False).hexdigest(), 16) % len(palette)]
    image = Image.new("RGB", (size, size), color)
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 140)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), letter, font=font)
    x = (size - (bbox[2] - bbox[0])) / 2
    y = (size - (bbox[3] - bbox[1])) / 2 - 8
    draw.text((x, y), letter, fill="white", font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{letter.lower()}_avatar.png")


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        if not password:
            raise ValueError("Password is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to=avatar_upload_to)
    phone = models.CharField(max_length=12, unique=True)
    github_url = models.URLField(blank=True, validators=[validate_github_url])
    about = models.CharField(max_length=256, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    date_joined = models.DateTimeField(default=timezone.now, editable=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    favorites = models.ManyToManyField("projects.Project", blank=True, related_name="interested_users")

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

# Create your models here.