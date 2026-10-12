from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.http import urlencode

from .models import CustomUser


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class LoginRedirectTests(TestCase):
    def setUp(self):
        self.password = "test-password-2026!"
        self.user = CustomUser.objects.create_user(
            email="student@example.com",
            first_name="Marie",
            last_name="Pierre",
            birth_year=2004,
            password=self.password,
        )

    def test_login_returns_to_protected_page_that_required_authentication(self):
        target = reverse("certificates:mine")
        response = self.client.get(target)
        self.assertEqual(response.status_code, 302)

        login_path = response["Location"]
        login_page = self.client.get(login_path)
        self.assertEqual(login_page.status_code, 200)
        self.assertContains(login_page, f'value="{target}"')

        login_response = self.client.post(
            login_path,
            {
                "username": self.user.email,
                "password": self.password,
                "next": target,
            },
        )
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response["Location"], target)

    def test_login_rejects_external_next_url(self):
        login_path = f"{reverse('accounts:login')}?{urlencode({'next': 'https://attacker.example/steal'})}"
        response = self.client.post(
            login_path,
            {
                "username": self.user.email,
                "password": self.password,
                "next": "https://attacker.example/steal",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("courses:course_list"))

    def test_login_page_renders_when_next_is_missing(self):
        response = self.client.get(reverse("accounts:login"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next_url"], "")

    def test_failed_login_preserves_next_url_for_retry(self):
        target = reverse("certificates:mine")
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": self.user.email,
                "password": "incorrect-password",
                "next": target,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next_url"], target)
        self.assertContains(response, f'value="{target}"')

    def test_authenticated_login_page_honors_safe_next_url(self):
        self.client.force_login(self.user)
        target = reverse("ranking:leaderboard")
        response = self.client.get(
            f"{reverse('accounts:login')}?{urlencode({'next': target})}"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], target)
