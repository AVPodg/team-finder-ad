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

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["status"], "ok")
        user = User.objects.get(email="alice@example.com")
        self.assertEqual(str(self.client.session.get("_auth_user_id")), str(user.id))

    def test_registration_returns_form_errors_for_invalid_data(self):
        response = self.client.post(
            reverse("users:register"),
            {
                "name": "Alice",
                "surname": "Smith",
                "email": "alice@example.com",
                "phone": "invalid-phone",
                "password": "password123",
            },
        )

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertIn("phone", payload["errors"])

    def test_login_returns_json(self):
        user = User.objects.create_user(
            email="alice@example.com",
            password="password123",
            name="Alice",
            surname="Smith",
            phone="+79990000005",
        )

        response = self.client.post(
            reverse("users:login"),
            {
                "email": "alice@example.com",
                "password": "password123",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["user_id"], user.id)

    def test_change_password_returns_json(self):
        user = User.objects.create_user(
            email="alice@example.com",
            password="password123",
            name="Alice",
            surname="Smith",
            phone="+79990000006",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("users:change-password"),
            {
                "old_password": "password123",
                "new_password1": "new-password-123",
                "new_password2": "new-password-123",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-password-123"))

    def test_profile_is_edited_via_users_root_route(self):
        user = User.objects.create_user(
            email="profile@example.com",
            password="password123",
            name="Old",
            surname="Name",
            phone="+79990000007",
        )
        self.client.force_login(user)

        get_response = self.client.get("/users/")
        self.assertEqual(get_response.status_code, 200)

        post_response = self.client.post(
            "/users/",
            {
                "name": "New",
                "surname": "Name",
                "email": "profile@example.com",
                "about": "Updated profile",
                "phone": "+79990000007",
                "github_url": "",
            },
        )

        self.assertRedirects(post_response, reverse("users:detail", args=[user.id]))
        user.refresh_from_db()
        self.assertEqual(user.name, "New")

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
