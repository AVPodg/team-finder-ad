import json
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from users.forms import EmailAuthenticationForm, RegisterForm, UserUpdateForm
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


def _skill_payload(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return {}


def register_view(request):
    if request.user.is_authenticated:
        return redirect("projects:list")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Регистрация завершена.")
        return redirect("projects:list")
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("projects:list")

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("projects:list")
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def detail_view(request, user_id: int):
    profile_user = get_object_or_404(
        User.objects.prefetch_related("skills", "owned_projects__participants"),
        pk=user_id,
    )
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required
def edit_profile_view(request):
    form = UserUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("users:detail", user_id=request.user.id)
    return render(request, "users/edit_profile.html", {"form": form, "user": request.user})


def list_view(request):
    users = User.objects.prefetch_related("skills").order_by("-created_at", "-id")
    task_version = _task_version()
    context = {}

    if task_version == "1":
        active_filter = request.GET.get("filter", "")
        if request.user.is_authenticated:
            if active_filter == "owners-of-favorite-projects":
                users = users.filter(owned_projects__favorited_by=request.user)
            elif active_filter == "owners-of-participating-projects":
                users = users.filter(owned_projects__participants=request.user)
            elif active_filter == "interested-in-my-projects":
                users = users.filter(favorites__owner=request.user).exclude(pk=request.user.pk)
            elif active_filter == "participants-of-my-projects":
                users = users.filter(participated_projects__owner=request.user).exclude(pk=request.user.pk)
        users = users.distinct()
        context["active_filter"] = active_filter
        context["query_prefix"] = _query_prefix(request, "filter")
    elif task_version == "2":
        active_skill = request.GET.get("skill", "").strip()
        if active_skill:
            users = users.filter(skills__name=active_skill).distinct()
        context["active_skill"] = active_skill
        context["all_skills"] = list(Skill.objects.values_list("name", flat=True))
        context["query_prefix"] = _query_prefix(request, "skill")
    else:
        context["query_prefix"] = ""

    page_obj = _paginate(request, users)
    context.update({"page_obj": page_obj})
    return render(request, "users/participants.html", context)


@login_required
def change_password_view(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return redirect("users:detail", user_id=request.user.id)
    return render(request, "users/change_password.html", {"form": form})


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
def add_skill_view(request, user_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "auth_required"}, status=403)
    if request.user.id != user_id:
        return JsonResponse({"status": "forbidden"}, status=403)

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

    request.user.skills.add(skill)
    return JsonResponse({"id": skill.id, "name": skill.name})


@require_http_methods(["POST"])
def remove_skill_view(request, user_id: int, skill_id: int):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "auth_required"}, status=403)
    if request.user.id != user_id:
        return JsonResponse({"status": "forbidden"}, status=403)

    request.user.skills.remove(get_object_or_404(Skill, pk=skill_id))
    return JsonResponse({"status": "ok"})

# Create your views here.