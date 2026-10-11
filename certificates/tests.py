from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import CustomUser
from courses.models import Course, Lecon, Module, Unite
from progress.models import ProgresCours, ProgresLecon

from .models import Certificate, CertificateSigner
from .services import (
    CertificateDeliveryError,
    course_is_complete,
    issue_certificate,
)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    BREVO_API_KEY="test-brevo-key",
    DEFAULT_FROM_EMAIL="certificates@example.com",
    SITE_URL="https://educadim.example",
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    },
)
class CertificateWorkflowTests(TestCase):
    def setUp(self):
        self.student = CustomUser.objects.create_user(
            email="student@example.com",
            first_name="Marie",
            last_name="Pierre",
            birth_year=2004,
            password="Test-password-2026!",
        )
        self.staff = CustomUser.objects.create_user(
            email="staff@example.com",
            first_name="Alex",
            last_name="Jean",
            birth_year=1980,
            password="Test-password-2026!",
            is_staff=True,
        )
        self.course = Course.objects.create(titre="Formation professionnelle")
        unit = Unite.objects.create(cours=self.course, titre="Unité 1")
        module = Module.objects.create(unite=unit, titre="Module 1")
        self.lesson = Lecon.objects.create(module=module, titre="Leçon 1")
        self.progress = ProgresCours.objects.create(
            utilisateur=self.student,
            cours=self.course,
            pourcentage=100,
        )
        self.certificate = Certificate.objects.get(
            student=self.student,
            course=self.course,
        )

    def mark_course_complete(self):
        ProgresLecon.objects.create(
            utilisateur=self.student,
            lecon=self.lesson,
            statut="termine",
        )

    def test_100_percent_creates_request_but_not_an_issued_certificate(self):
        self.assertEqual(self.certificate.status, Certificate.Status.PENDING)
        self.assertIsNone(self.certificate.issued_at)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(course_is_complete(self.student, self.course))

    def test_qr_verification_is_not_public_before_approval(self):
        url = reverse(
            "certificates:verify",
            kwargs={"public_id": self.certificate.public_id},
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_only_the_student_can_submit_name_corrections(self):
        other_student = CustomUser.objects.create_user(
            email="other@example.com",
            first_name="Jean",
            last_name="Paul",
            birth_year=2003,
            password="Test-password-2026!",
        )
        self.client.force_login(other_student)
        url = reverse(
            "certificates:submit_details",
            kwargs={"public_id": self.certificate.public_id},
        )
        response = self.client.post(
            url,
            {"student_name": "Someone Else", "student_note": ""},
        )
        self.assertEqual(response.status_code, 404)
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.student_name, "Marie Pierre")

    def test_student_resubmits_after_correction_request(self):
        self.certificate.status = Certificate.Status.CORRECTION
        self.certificate.review_note = "Vérifiez l'orthographe du nom."
        self.certificate.save()
        self.client.force_login(self.student)
        url = reverse(
            "certificates:submit_details",
            kwargs={"public_id": self.certificate.public_id},
        )
        response = self.client.post(
            url,
            {
                "student_name": "Marie P. Pierre",
                "student_note": "Voici l'orthographe confirmée.",
            },
        )
        self.assertRedirects(response, reverse("certificates:mine"))
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.PENDING)
        self.assertEqual(self.certificate.student_name, "Marie P. Pierre")

    def test_staff_approval_emails_pdf_and_enables_verification(self):
        self.mark_course_complete()
        signer = CertificateSigner.objects.create(
            name="Directrice académique",
            title="Directrice",
        )
        self.client.force_login(self.staff)
        url = reverse(
            "certificates:review",
            kwargs={"public_id": self.certificate.public_id},
        )
        response = self.client.post(
            url,
            {
                "decision": "issue",
                "student_name": "Marie Pierre",
                "review_note": "",
                "signers": [str(signer.pk)],
            },
        )

        self.assertRedirects(response, reverse("certificates:review_queue"))
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.ISSUED)
        self.assertEqual(self.certificate.reviewed_by, self.staff)
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue(mail.outbox[0].attachments)
        filename, pdf_content, mime_type = mail.outbox[0].attachments[0]
        self.assertTrue(filename.endswith(".pdf"))
        self.assertEqual(mime_type, "application/pdf")
        self.assertTrue(pdf_content.startswith(b"%PDF"))

        verify_url = reverse(
            "certificates:verify",
            kwargs={"public_id": self.certificate.public_id},
        )
        verify_response = self.client.get(verify_url)
        self.assertEqual(verify_response.status_code, 200)
        self.assertContains(verify_response, "Certificat valide")

        download_url = reverse(
            "certificates:download",
            kwargs={"public_id": self.certificate.public_id},
        )
        pdf_response = self.client.get(download_url)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertEqual(pdf_response["Cache-Control"], "private, no-store")
        self.assertEqual(
            b"".join(pdf_response.streaming_content),
            pdf_content,
        )
        with self.assertRaises(CertificateDeliveryError):
            issue_certificate(self.certificate, self.staff)
        self.assertEqual(len(mail.outbox), 1)

        revoke_response = self.client.post(
            url,
            {"decision": "revoke", "review_note": "Erreur de vérification."},
        )
        self.assertRedirects(revoke_response, reverse("certificates:review_queue"))
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.REVOKED)
        self.assertContains(self.client.get(verify_url), "Certificat révoqué")
        self.assertEqual(self.client.get(download_url).status_code, 404)

    def test_staff_cannot_issue_when_lesson_completion_is_missing(self):
        signer = CertificateSigner.objects.create(name="Équipe", title="Direction")
        self.client.force_login(self.staff)
        url = reverse(
            "certificates:review",
            kwargs={"public_id": self.certificate.public_id},
        )
        response = self.client.post(
            url,
            {
                "decision": "issue",
                "student_name": "Marie Pierre",
                "review_note": "",
                "signers": [str(signer.pk)],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.PENDING)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, "progression réelle du cours")

    def test_staff_can_request_correction_without_sending_email(self):
        self.client.force_login(self.staff)
        url = reverse(
            "certificates:review",
            kwargs={"public_id": self.certificate.public_id},
        )
        response = self.client.post(
            url,
            {
                "decision": "correction",
                "student_name": "Marie P.",
                "review_note": "Merci de confirmer l'orthographe du nom.",
                "signers": [],
            },
        )
        self.assertRedirects(response, reverse("certificates:review_queue"))
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.CORRECTION)
        self.assertEqual(len(mail.outbox), 0)

    def test_missing_brevo_configuration_does_not_issue_certificate(self):
        self.mark_course_complete()
        signer = CertificateSigner.objects.create(name="Équipe", title="Direction")
        self.client.force_login(self.staff)
        url = reverse(
            "certificates:review",
            kwargs={"public_id": self.certificate.public_id},
        )
        with override_settings(BREVO_API_KEY=""):
            response = self.client.post(
                url,
                {
                    "decision": "issue",
                    "student_name": "Marie Pierre",
                    "review_note": "",
                    "signers": [str(signer.pk)],
                },
            )
        self.assertEqual(response.status_code, 200)
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.status, Certificate.Status.PENDING)
        self.assertIsNone(self.certificate.issued_at)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, "clé Brevo manquante")
