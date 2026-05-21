from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from projects.models import Project
from users.models import User


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
        redirect_response = self.client.get("/")
        self.assertRedirects(redirect_response, "/projects/list/")

    def test_project_list_is_sorted_from_newest_to_oldest(self):
        older = Project.objects.create(name="Old", owner=self.owner)
        newer = Project.objects.create(name="New", owner=self.owner)

        response = self.client.get(reverse("projects:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["page_obj"].object_list[:2]), [newer, older])

    def test_create_project_requires_login(self):
        response = self.client.get("/projects/create-project/")

        self.assertRedirects(response, "/users/login/?next=/projects/create-project/")

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

    def test_project_rejects_non_github_url(self):
        project = Project(name="Bad", owner=self.owner, github_url="https://gitlab.com/team/project")

        with self.assertRaises(ValidationError):
            project.full_clean()

# Create your tests here.