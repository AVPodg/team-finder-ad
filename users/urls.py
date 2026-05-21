from django.urls import path

from users import views

app_name = "users"

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("edit-profile/", views.edit_profile_view, name="edit-profile"),
    path("change-password/", views.change_password_view, name="change-password"),
    path("list/", views.list_view, name="list"),
    path("<int:user_id>/", views.detail_view, name="detail"),
]