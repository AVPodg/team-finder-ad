from django.test import TestCase, override_settings
from django.urls import reverse

from projects.models import Project
from users.models import Skill, User


class ProjectTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            email="owner@example.com",
            password="password123",
            name="Owner",
            surname="User",
            phone="+79990000001",
        )
        self.member = User.objects.create_user(
            email="member@example.com",
            password="password123",
            name="Member",
            surname="User",
            phone="+79990000002",
        )
        self.project = Project.objects.create(
            name="Project One",
            description="Description",
            owner=self.owner,
        )

    def test_project_list_is_paginated(self):
        for number in range(13):
            Project.objects.create(
                name=f"Project {number}",
                description="Description",
                owner=self.owner,
            )

        response = self.client.get(reverse("projects:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["page_obj"].object_list), 12)
        root_response = self.client.get("/projects/")
        self.assertEqual(root_response.status_code, 200)

    def test_favorite_participation_and_complete_endpoints(self):
        self.client.force_login(self.member)

        favorite_response = self.client.post(reverse("projects:toggle-favorite", args=[self.project.id]))
        self.assertEqual(favorite_response.status_code, 200)
        self.assertTrue(self.member.favorites.filter(pk=self.project.pk).exists())

        participate_response = self.client.post(reverse("projects:toggle-participate", args=[self.project.id]))
        self.assertEqual(participate_response.status_code, 200)
        self.assertTrue(self.project.participants.filter(pk=self.member.pk).exists())

        self.client.force_login(self.owner)
        complete_response = self.client.post(reverse("projects:complete", args=[self.project.id]))
        self.assertEqual(complete_response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, Project.STATUS_CLOSED)

    @override_settings(TASK_VERSION="3")
    def test_project_skill_endpoints_and_filter(self):
        self.client.force_login(self.owner)
        add_response = self.client.post(
            reverse("projects:add-skill", args=[self.project.id]),
            data='{"name":"Python"}',
            content_type="application/json",
        )

        self.assertEqual(add_response.status_code, 200)
        skill = Skill.objects.get(name="Python")
        self.assertTrue(self.project.skills.filter(pk=skill.pk).exists())

        list_response = self.client.get(reverse("projects:list"), {"skill": "Python"})
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list(list_response.context["page_obj"].object_list), [self.project])

        remove_response = self.client.post(reverse("projects:remove-skill", args=[self.project.id, skill.id]))
        self.assertEqual(remove_response.status_code, 200)
        self.assertFalse(self.project.skills.filter(pk=skill.pk).exists())

# Create your tests here.
