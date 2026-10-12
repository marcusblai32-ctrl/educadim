from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from .models import PointsUtilisateur
from .services import get_ranked_users, normalize_period, render_palmares_pdf


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class PalmaresTests(TestCase):
    def setUp(self):
        self.student_one = CustomUser.objects.create_user(
            email="lea@example.com",
            first_name="Léa",
            last_name="Jean",
            birth_year=2002,
            password="test-password",
        )
        self.student_two = CustomUser.objects.create_user(
            email="max@example.com",
            first_name="Max",
            last_name="Pierre",
            birth_year=2001,
            password="test-password",
        )
        self.points_one = PointsUtilisateur.objects.create(
            utilisateur=self.student_one,
            total=120,
            semaine=10,
            mois=35,
        )
        self.points_two = PointsUtilisateur.objects.create(
            utilisateur=self.student_two,
            total=75,
            semaine=20,
            mois=18,
        )

    def test_periods_use_the_matching_stored_point_total(self):
        self.assertEqual(
            list(get_ranked_users("total")),
            [self.points_one, self.points_two],
        )
        self.assertEqual(
            list(get_ranked_users("semaine")),
            [self.points_two, self.points_one],
        )
        self.assertEqual(
            list(get_ranked_users("mois")),
            [self.points_one, self.points_two],
        )

    def test_invalid_period_defaults_to_total(self):
        self.assertEqual(normalize_period("unknown"), "total")

    def test_palmares_pdf_is_valid_pdf(self):
        pdf_bytes = render_palmares_pdf(
            "total",
            get_ranked_users("total"),
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))

    def test_authenticated_student_can_download_selected_period_pdf(self):
        self.client.force_login(self.student_one)
        response = self.client.get(
            reverse("ranking:palmares_pdf"),
            {"periode": "semaine"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(
            'educadim-palmares-semaine.pdf',
            response["Content-Disposition"],
        )
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_certificate_home_links_to_palmares(self):
        self.client.force_login(self.student_one)
        response = self.client.get(reverse("certificates:mine"))
        self.assertContains(response, reverse("ranking:leaderboard"))
        self.assertContains(response, reverse("ranking:palmares_pdf"))

    def test_homepage_links_to_certificate_home(self):
        self.client.force_login(self.student_one)
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("certificates:mine"))
