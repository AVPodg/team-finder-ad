from django.urls import path

from projects import views

app_name = "projects"

urlpatterns = [
    path("", views.list_view),
    path("list/", views.list_view, name="list"),
    path("favorites/", views.favorites_view, name="favorites"),
    path("create-project/", views.create_view, name="create"),
    path("<int:project_id>/toggle-favorite/", views.toggle_favorite_view, name="toggle-favorite"),
    path("<int:project_id>/toggle-participate/", views.toggle_participate_view, name="toggle-participate"),
    path("<int:project_id>/complete/", views.complete_view, name="complete"),
    path("<int:project_id>/edit/", views.edit_view, name="edit"),
    path("<int:project_id>/", views.detail_view, name="detail"),
]
