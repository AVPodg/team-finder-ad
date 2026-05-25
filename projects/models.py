from django.conf import settings
from django.db import models
from django.urls import reverse

from projects.constants import MAX_PROJECT_NAME_LENGTH, STATUS_MAX_LENGTH
from users.models import validate_github_url


class Project(models.Model):
    STATUS_OPEN = "open"
    STATUS_CLOSED = "closed"
    STATUS_CHOICES = (
        (STATUS_OPEN, "Open"),
        (STATUS_CLOSED, "Closed"),
    )

    name = models.CharField(max_length=MAX_PROJECT_NAME_LENGTH)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(
        blank=True,
        validators=[validate_github_url]
    )
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name="participated_projects",
    )

    class Meta:
        ordering = ("-created_at", "-id")

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("projects:detail", kwargs={"pk": self.pk})
    