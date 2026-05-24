from django import forms

from projects.models import Project


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ("name", "description", "github_url", "status")
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
            "status": "Статус",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Введите название проекта"}),
            "description": forms.Textarea(attrs={"rows": 6, "placeholder": "Опишите идею проекта"}),
            "github_url": forms.URLInput(attrs={"placeholder": "https://github.com/owner/repository"}),
            "status": forms.Select(),
        }
        