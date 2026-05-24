# projects/services.py
from django.core.paginator import Paginator
from django.db.models import QuerySet
from django.http import HttpRequest

from projects.constants import PROJECTS_PER_PAGE
from projects.models import Project
from users.models import User


def get_projects_queryset():
    return Project.objects.select_related("owner").prefetch_related("participants")


def prime_request_user(request: HttpRequest):
    if request.user.is_authenticated:
        request.user = User.objects.prefetch_related("favorites").get(
            pk=request.user.pk
        )


def paginate(request: HttpRequest, queryset: QuerySet, per_page: int = PROJECTS_PER_PAGE):
    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get("page"))