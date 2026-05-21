from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from users.forms import EmailAuthenticationForm, RegisterForm, UserUpdateForm
from users.models import User


def _query_prefix(request, *keys: str) -> str:
    params = request.GET.copy()
    params.pop("page", None)
    allowed = {key: value for key, value in params.items() if key in keys and value}
    return f"{urlencode(allowed)}&" if allowed else ""


def _paginate(request, queryset):
    paginator = Paginator(queryset, 12)
    return paginator.get_page(request.GET.get("page"))


def _form_errors(form):
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


def register_view(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            return JsonResponse({"status": "error", "errors": {"__all__": ["Пользователь уже авторизован."]}}, status=409)
        return redirect("projects:list")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Регистрация завершена.")
        return JsonResponse({"status": "ok", "user_id": user.id, "email": user.email}, status=201)
    if request.method == "POST":
        return JsonResponse({"status": "error", "errors": _form_errors(form)}, status=400)
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            return JsonResponse({"status": "error", "errors": {"__all__": ["Пользователь уже авторизован."]}}, status=409)
        return redirect("projects:list")

    form = EmailAuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        return JsonResponse({"status": "ok", "user_id": user.id, "email": user.email})
    if request.method == "POST":
        return JsonResponse({"status": "error", "errors": _form_errors(form)}, status=400)
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("projects:list")


def detail_view(request, user_id: int):
    profile_user = get_object_or_404(
        User.objects.prefetch_related("owned_projects__participants"),
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
    users = User.objects.prefetch_related("owned_projects", "favorites", "participated_projects").order_by("id")
    active_filter = request.GET.get("filter", "")
    if request.user.is_authenticated:
        if active_filter == "owners-of-favorite-projects":
            users = users.filter(owned_projects__interested_users=request.user)
        elif active_filter == "owners-of-participating-projects":
            users = users.filter(owned_projects__participants=request.user)
        elif active_filter == "interested-in-my-projects":
            users = users.filter(favorites__owner=request.user).exclude(pk=request.user.pk)
        elif active_filter == "participants-of-my-projects":
            users = users.filter(participated_projects__owner=request.user).exclude(pk=request.user.pk)
    users = users.distinct()
    page_obj = _paginate(request, users)
    context = {
        "active_filter": active_filter,
        "query_prefix": _query_prefix(request, "filter"),
        "page_obj": page_obj,
    }
    return render(request, "users/participants.html", context)


def change_password_view(request):
    if not request.user.is_authenticated:
        if request.method == "POST":
            return JsonResponse({"status": "error", "errors": {"__all__": ["Требуется авторизация."]}}, status=403)
        return redirect("users:login")
    form = PasswordChangeForm(request.user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        return JsonResponse({"status": "ok"})
    if request.method == "POST":
        return JsonResponse({"status": "error", "errors": _form_errors(form)}, status=400)
    return render(request, "users/change_password.html", {"form": form})