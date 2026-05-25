import json
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from projects.constants import PROJECTS_PER_PAGE
from projects.forms import ProjectForm
from projects.models import Project
from projects.services import (
    get_projects_queryset,
    paginate,
    prime_request_user,
)
from users.models import User


def list_view(request):
    prime_request_user(request)

    projects = get_projects_queryset()

    search_query = request.GET.get('search', '')
    if search_query and hasattr(search_query, 'strip'):
        search_query = search_query.strip()
        projects = projects.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    page_obj = paginate(request, projects)

    query_prefix = f"search={search_query}" if search_query else ""

    context = {
        "projects": page_obj.object_list,
        "page_obj": page_obj,
        "query_prefix": query_prefix,
    }
    return render(request, "projects/project_list.html", context)


def detail_view(request, project_id: int):
    prime_request_user(request)
    project = get_object_or_404(
        get_projects_queryset(),
        pk=project_id,
    )
    return render(
        request,
        "projects/project-details.html",
        {"project": project}
    )


@login_required
def create_view(request):
    form = ProjectForm(request.POST or None)
    if form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        form.save_m2m()
        return redirect("projects:detail", project_id=project.id)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": False}
    )


@login_required
def edit_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)

    if project.owner_id != request.user.id and not request.user.is_staff:
        return redirect("projects:detail", project_id=project.id)

    form = ProjectForm(request.POST or None, instance=project)
    if form.is_valid():
        project = form.save()
        return redirect("projects:detail", project_id=project.id)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True}
    )


@login_required
def favorites_view(request):
    prime_request_user(request)
    projects = request.user.favorites.select_related("owner").prefetch_related(
        "participants"
    )
    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": projects}
    )


@require_http_methods(["POST"])
def toggle_favorite_view(request, project_id: int):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "auth_required"},
            status=HTTPStatus.FORBIDDEN
        )

    project = get_object_or_404(Project, pk=project_id)
    is_favorite = request.user.favorites.filter(pk=project.pk).exists()
    if is_favorite:
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": not is_favorite})


@require_http_methods(["POST"])
def toggle_participate_view(request, project_id: int):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "auth_required"},
            status=HTTPStatus.FORBIDDEN
        )

    project = get_object_or_404(Project, pk=project_id)

    if project.owner_id == request.user.id or project.status != Project.STATUS_OPEN:
        return JsonResponse(
            {"status": "forbidden"},
            status=HTTPStatus.FORBIDDEN
        )

    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)

    return JsonResponse({"status": "ok", "joined": not is_participant})


@require_http_methods(["POST"])
def complete_view(request, project_id: int):
    if not request.user.is_authenticated:
        return JsonResponse(
            {"status": "auth_required"},
            status=HTTPStatus.FORBIDDEN
        )

    project = get_object_or_404(Project, pk=project_id)

    if project.owner_id != request.user.id and not request.user.is_staff:
        return JsonResponse(
            {"status": "forbidden"},
            status=HTTPStatus.FORBIDDEN
        )

    if project.status != Project.STATUS_OPEN:
        return JsonResponse(
            {"status": "invalid"},
            status=HTTPStatus.BAD_REQUEST
        )

    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])

    return JsonResponse({"status": "ok", "project_status": "closed"})


@require_http_methods(["POST"])
@login_required
def delete_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id and not request.user.is_staff:
        return HttpResponseForbidden("Вы не можете удалить этот проект.")

    project.delete()
    return JsonResponse({"status": "ok"})
