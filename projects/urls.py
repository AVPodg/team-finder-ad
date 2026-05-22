from django.urls import path
from projects import views

app_name = "projects"

urlpatterns = [
    # Возвращаем роут, который запрашивает твой фронтенд и редиректы
    path("", views.list_view, name="list"),
    path("list/", views.list_view, name="list-explicit"),
    
    # Статические страницы (строго ДО путей с ID)
    path("create-project/", views.create_view, name="create"),
    path("favorites/", views.favorites_view, name="favorites"),
    
    # Детальная страница конкретного проекта
    # Ограничитель <int:> гарантирует, что Django НЕ перепутает ID со словами "create" или "favorites"
    path("<int:project_id>/", views.detail_view, name="detail"),
    
    # Управление проектом
    path("<int:project_id>/edit/", views.edit_view, name="edit"),
    path("<int:project_id>/delete/", views.delete_view, name="delete"),
    path("<int:project_id>/complete/", views.complete_view, name="complete"),
    
    # AJAX-эндпоинты для лайков и участия
    path("<int:project_id>/toggle-favorite/", views.toggle_favorite_view, name="toggle-favorite"),
    path("<int:project_id>/toggle-participate/", views.toggle_participate_view, name="toggle-participate"),
]