from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse

from users.models import Skill, User


@override_settings(TASK_VERSION="2")
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

    def test_registration_and_user_skill_endpoints(self):
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

        self.assertRedirects(response, reverse("users:login"))
        user = User.objects.get(email="alice@example.com")
        self.client.force_login(user)

        add_response = self.client.post(
            reverse("users:add-skill", args=[user.id]),
            data='{"name":"Django"}',
            content_type="application/json",
        )
        self.assertEqual(add_response.status_code, 200)
        skill = Skill.objects.get(name="Django")
        self.assertTrue(user.skills.filter(pk=skill.pk).exists())

        remove_response = self.client.post(reverse("users:remove-skill", args=[user.id, skill.id]))
        self.assertEqual(remove_response.status_code, 200)
        self.assertFalse(user.skills.filter(pk=skill.pk).exists())

# Create your tests here.
