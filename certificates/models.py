import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class CertificateSigner(models.Model):
    name = models.CharField(max_length=160, verbose_name="Nom du signataire")
    title = models.CharField(max_length=160, verbose_name="Fonction")
    signature = models.ImageField(
        upload_to="certificates/signatures/",
        blank=True,
        null=True,
        verbose_name="Image de signature",
    )
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre")
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("order", "name")
        verbose_name = "Signataire de certificat"
        verbose_name_plural = "Signataires de certificats"

    def __str__(self):
        return f"{self.name} — {self.title}"


class Certificate(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente de vérification"
        CORRECTION = "correction", "Correction demandée"
        ISSUED = "issued", "Délivré"
        REVOKED = "revoked", "Révoqué"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="Identifiant de vérification",
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="certificates",
        verbose_name="Étudiant",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="certificates",
        verbose_name="Cours",
    )
    student_name = models.CharField(
        max_length=180,
        verbose_name="Nom à imprimer sur le certificat",
    )
    completed_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Date de fin du cours",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        verbose_name="Statut",
    )
    signers = models.ManyToManyField(
        CertificateSigner,
        blank=True,
        related_name="certificates",
        verbose_name="Signataires",
    )
    student_note = models.TextField(blank=True, verbose_name="Note de l'étudiant")
    review_note = models.TextField(blank=True, verbose_name="Note de vérification")
    pdf_content = models.BinaryField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="Copie PDF délivrée",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates_reviewed",
        verbose_name="Vérifié par",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de vérification",
    )
    issued_at = models.DateTimeField(null=True, blank=True, verbose_name="Date de délivrance")
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name="Date d'envoi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("student", "course"),
                name="unique_certificate_per_student_course",
            )
        ]
        verbose_name = "Certificat"
        verbose_name_plural = "Certificats"

    def __str__(self):
        return f"{self.student_name} — {self.course.get_titre()} ({self.get_status_display()})"

    @property
    def certificate_number(self):
        return self.public_id.hex[:12].upper()

    @property
    def is_valid(self):
        return self.status == self.Status.ISSUED
