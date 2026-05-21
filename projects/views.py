from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from projects.forms import ProjectForm
from projects.models import Project
from users.models import User


def _paginate(request, queryset):
    paginator = Paginator(queryset, 12)
    return paginator.get_page(request.GET.get("page"))


def _prime_request_user(request):
    if request.user.is_authenticated:
        request.user = User.objects.prefetch_related("favorites").get(pk=request.user.pk)


def list_view(request):
    _prime_request_user(request)
    projects = Project.objects.select_related("owner").prefetch_related("participants")
    page_obj = _paginate(request, projects)
    context = {
        "projects": page_obj.object_list,
        "page_obj": page_obj,
        "query_prefix": "",
    }
    return render(request, "projects/project_list.html", context)


def detail_view(request, project_id: int):
    _prime_request_user(request)
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants"),
        pk=project_id,
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def create_view(request):
    form = ProjectForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.owner = request.user
        project.save()
        form.save_m2m()
        return redirect("projects:detail", project_id=project.id)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": False})


@login_required
def edit_view(request, project_id: int):
    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    form = ProjectForm(request.POST or None, instance=project)
    if request.method == "POST" and form.is_valid():
        project = form.save()
        return redirect("projects:detail", project_id=project.id)
    return render(request, "projects/create-project.html", {"form": form, "is_edit": True})


@login_required
def favorites_view(request):
    _prime_request_user(request)
    projects = request.user.favorites.select_related("owner").prefetch_related("participants")
    return render(request, "projects/favorite_projects.html", {"projects": projects})


@require_http_methods(["POST"])
def toggle_favorite_view(request, project_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "auth_required"}, status=403)

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
        return JsonResponse({"status": "auth_required"}, status=403)

    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id == request.user.id or project.status != Project.STATUS_OPEN:
        return JsonResponse({"status": "forbidden"}, status=403)

    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": not is_participant})


@require_http_methods(["POST"])
def complete_view(request, project_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "auth_required"}, status=403)

    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    if project.status != Project.STATUS_OPEN:
        return JsonResponse({"status": "invalid"}, status=400)
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok"})