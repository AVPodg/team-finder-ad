import json
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from projects.forms import ProjectForm
from projects.models import Project
from users.models import Skill, User


def _task_version() -> str:
    return str(getattr(settings, "TASK_VERSION", "1"))


def _query_prefix(request, *keys: str) -> str:
    params = request.GET.copy()
    params.pop("page", None)
    allowed = {key: value for key, value in params.items() if key in keys and value}
    return f"{urlencode(allowed)}&" if allowed else ""


def _paginate(request, queryset):
    paginator = Paginator(queryset, 12)
    return paginator.get_page(request.GET.get("page"))


def _prime_request_user(request):
    if request.user.is_authenticated:
        request.user = User.objects.prefetch_related("favorites").get(pk=request.user.pk)


def _skill_payload(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


def list_view(request):
    _prime_request_user(request)
    projects = Project.objects.select_related("owner").prefetch_related("participants", "skills")
    active_skill = ""
    if _task_version() == "3":
        active_skill = request.GET.get("skill", "").strip()
        if active_skill:
            projects = projects.filter(skills__name=active_skill).distinct()

    page_obj = _paginate(request, projects)
    context = {
        "projects": page_obj.object_list,
        "page_obj": page_obj,
        "active_skill": active_skill,
        "all_skills": list(Skill.objects.values_list("name", flat=True)) if _task_version() == "3" else [],
        "query_prefix": _query_prefix(request, "skill"),
    }
    return render(request, "projects/project_list.html", context)


def detail_view(request, project_id: int):
    _prime_request_user(request)
    project = get_object_or_404(
        Project.objects.select_related("owner").prefetch_related("participants", "skills"),
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
    projects = request.user.favorites.select_related("owner").prefetch_related("participants", "skills")
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
    return JsonResponse({"status": "ok", "favorite": not is_favorite})


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
    project.status = Project.STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok"})


@require_GET
@login_required
def skills_view(request):
    query = request.GET.get("q", "").strip()
    skills = Skill.objects.all()
    if query:
        skills = skills.filter(name__icontains=query)
    data = [{"id": skill.id, "name": skill.name} for skill in skills[:10]]
    return JsonResponse(data, safe=False)


@require_http_methods(["POST"])
def add_skill_view(request, project_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "auth_required"}, status=403)

    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    payload = _skill_payload(request)
    skill = None
    skill_id = payload.get("skill_id")
    if skill_id:
        skill = get_object_or_404(Skill, pk=skill_id)
    else:
        name = (payload.get("name") or "").strip()
        if not name:
            return JsonResponse({"status": "invalid"}, status=400)
        skill = Skill.objects.filter(name__iexact=name).first()
        if skill is None:
            skill = Skill.objects.create(name=name[:64])

    project.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@require_http_methods(["POST"])
def remove_skill_view(request, project_id: int, skill_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "auth_required"}, status=403)

    project = get_object_or_404(Project, pk=project_id, owner=request.user)
    project.skills.remove(get_object_or_404(Skill, pk=skill_id))
    return JsonResponse({"status": "ok"})

# Create your views here.
