from django import forms
from django.contrib.auth import authenticate

from users.models import User


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email", "phone", "password")
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
            "phone": "Телефон",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Введите имя"}),
            "surname": forms.TextInput(attrs={"placeholder": "Введите фамилию"}),
            "email": forms.EmailInput(attrs={"placeholder": "Введите email"}),
            "phone": forms.TextInput(attrs={"placeholder": "+79991234567"}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Введите email"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
    )

    error_messages = {
        "invalid_login": "Неверный email или пароль.",
        "inactive": "Учетная запись отключена.",
    }

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user_cache = authenticate(self.request, username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError(self.error_messages["invalid_login"])
            if not self.user_cache.is_active:
                raise forms.ValidationError(self.error_messages["inactive"])
        return cleaned_data

    def get_user(self):
        return self.user_cache


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("avatar", "name", "surname", "email", "about", "phone", "github_url")
        labels = {
            "avatar": "Аватар",
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "GitHub",
        }
        widgets = {
            "avatar": forms.FileInput(attrs={"class": "hidden", "accept": "image/*"}),
            "name": forms.TextInput(attrs={"placeholder": "Имя"}),
            "surname": forms.TextInput(attrs={"placeholder": "Фамилия"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email"}),
            "about": forms.Textarea(attrs={"rows": 4, "placeholder": "Расскажите о себе"}),
            "phone": forms.TextInput(attrs={"placeholder": "+79991234567"}),
            "github_url": forms.URLInput(attrs={"placeholder": "https://github.com/username"}),
        }


class AdminUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("email", "name", "surname", "phone")

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("password1") != cleaned_data.get("password2"):
            raise forms.ValidationError("Пароли не совпадают.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class AdminUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = "__all__"