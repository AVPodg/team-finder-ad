from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from users.models import User


class UserTests(TestCase):
    def test_user_phone_is_normalized_and_avatar_generated(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="password123",
            name="Alice",
            surname="Smith",
            phone="89991234567",
        )

        self.assertEqual(user.phone, "+79991234567")
        self.assertTrue(user.avatar.name)

    def test_user_rejects_non_github_profile_url(self):
        user = User(
            email="test@example.com",
            name="Alice",
            surname="Smith",
            phone="+79991234567",
            github_url="https://gitlab.com/alice",
        )

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_registration_logs_in_user(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Alice",
                "surname": "Smith",
                "email": "alice@example.com",
                "phone": "89991234567",
                "password": "password123",
            },
        )

        self.assertRedirects(response, reverse("projects:list"))
        user = User.objects.get(email="alice@example.com")
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(user.id))

    def test_users_list_is_sorted_by_id(self):
        first = User.objects.create_user(
            email="first@example.com",
            password="password123",
            name="First",
            surname="User",
            phone="+79990000001",
        )
        second = User.objects.create_user(
            email="second@example.com",
            password="password123",
            name="Second",
            surname="User",
            phone="+79990000002",
        )

        response = self.client.get(reverse("users:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [user.id for user in response.context["page_obj"].object_list[:2]],
            [first.id, second.id],
        )

    def test_users_filter_owners_of_favorite_projects(self):
        owner = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            name="Owner",
            surname="User",
            phone="+79990000003",
        )
        viewer = User.objects.create_user(
            email="viewer@example.com",
            password="password123",
            name="Viewer",
            surname="User",
            phone="+79990000004",
        )
        project = Project.objects.create(name="Project", owner=owner)
        viewer.favorites.add(project)

        self.client.force_login(viewer)
        response = self.client.get(reverse("users:list"), {"filter": "owners-of-favorite-projects"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["page_obj"].object_list), [owner])