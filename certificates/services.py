import io
import logging
from html import escape

import qrcode
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.urls import reverse
from django.utils import timezone, translation
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfgen import canvas

from courses.models import Lecon
from progress.models import ProgresLecon

from .models import Certificate

logger = logging.getLogger(__name__)


class CertificateDeliveryError(Exception):
    """Raised when a certificate cannot be safely issued and emailed."""


def course_is_complete(student, course):
    """Re-check lesson completion instead of trusting a saved percentage."""
    active_lessons = Lecon.objects.filter(
        module__unite__cours=course,
        actif=True,
    )
    total = active_lessons.count()
    if total == 0:
        return False
    completed = ProgresLecon.objects.filter(
        utilisateur=student,
        lecon__in=active_lessons,
        statut="termine",
    ).count()
    return completed >= total


def certificate_verification_url(certificate):
    with translation.override(settings.LANGUAGE_CODE):
        path = reverse(
            "certificates:verify",
            kwargs={"public_id": certificate.public_id},
        )
    return f"{settings.SITE_URL.rstrip('/')}{path}"


def render_certificate_pdf(certificate):
    """Create a print-ready landscape PDF with a QR code and selected signers."""
    page_width, page_height = landscape(A4)
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(page_width, page_height), pageCompression=1)
    pdf.setTitle(
        f"EducaDim certificate {certificate.certificate_number} — "
        f"{certificate.student_name}"
    )
    pdf.setAuthor(settings.SITE_NAME)

    navy = colors.HexColor("#14223d")
    gold = colors.HexColor("#bf9655")
    muted = colors.HexColor("#536176")
    paper = colors.HexColor("#fbf9f4")

    pdf.setFillColor(paper)
    pdf.rect(0, 0, page_width, page_height, stroke=0, fill=1)
    pdf.setStrokeColor(navy)
    pdf.setLineWidth(2.2)
    pdf.roundRect(24, 24, page_width - 48, page_height - 48, 7, stroke=1, fill=0)
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(0.9)
    pdf.roundRect(34, 34, page_width - 68, page_height - 68, 5, stroke=1, fill=0)

    center_x = page_width / 2
    pdf.setFillColor(navy)
    pdf.setFont("Times-Bold", 14)
    pdf.drawCentredString(center_x, page_height - 82, settings.SITE_NAME.upper())
    pdf.setStrokeColor(gold)
    pdf.setLineWidth(1.2)
    pdf.line(center_x - 95, page_height - 96, center_x + 95, page_height - 96)

    pdf.setFillColor(navy)
    pdf.setFont("Times-Bold", 27)
    pdf.drawCentredString(center_x, page_height - 143, "CERTIFICAT DE RÉUSSITE")
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(center_x, page_height - 174, "Ce certificat est décerné à")

    name_font_size = 31
    while name_font_size > 19 and pdf.stringWidth(
        certificate.student_name, "Times-Bold", name_font_size
    ) > page_width - 170:
        name_font_size -= 1
    pdf.setFillColor(gold)
    pdf.setFont("Times-Bold", name_font_size)
    pdf.drawCentredString(center_x, page_height - 220, certificate.student_name)

    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 11)
    pdf.drawCentredString(
        center_x,
        page_height - 253,
        "pour avoir terminé avec succès le cours",
    )
    course_lines = simpleSplit(
        certificate.course.get_titre(),
        "Times-Bold",
        18,
        page_width - 170,
    )[:2]
    pdf.setFillColor(navy)
    pdf.setFont("Times-Bold", 18)
    for index, line in enumerate(course_lines):
        pdf.drawCentredString(center_x, page_height - 283 - (index * 24), line)

    completed_date = timezone.localtime(certificate.completed_at).strftime("%d/%m/%Y")
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(
        center_x,
        page_height - 333,
        f"Parcours complété le {completed_date} — progression vérifiée à 100 %",
    )

    # Signatures are selected by an authorized reviewer and managed in Django Admin.
    signer_list = list(certificate.signers.filter(is_active=True)[:4])
    signature_y = 100
    available_width = page_width - 220
    slot_width = available_width / max(len(signer_list), 1)
    first_center = 110 + slot_width / 2
    for index, signer in enumerate(signer_list):
        signer_x = first_center + (index * slot_width)
        pdf.setStrokeColor(colors.HexColor("#aab2bd"))
        pdf.setLineWidth(0.65)
        pdf.line(signer_x - 67, signature_y + 29, signer_x + 67, signature_y + 29)
        if signer.signature:
            try:
                with signer.signature.open("rb") as signature_file:
                    image_bytes = io.BytesIO(signature_file.read())
                pdf.drawImage(
                    ImageReader(image_bytes),
                    signer_x - 48,
                    signature_y + 33,
                    width=96,
                    height=31,
                    preserveAspectRatio=True,
                    anchor="c",
                    mask="auto",
                )
            except (OSError, ValueError):
                logger.exception("Could not load certificate signature image")
        pdf.setFillColor(navy)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawCentredString(signer_x, signature_y + 13, signer.name[:42])
        pdf.setFillColor(muted)
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredString(signer_x, signature_y, signer.title[:48])

    verification_url = certificate_verification_url(certificate)
    qr_image = qrcode.make(verification_url, box_size=5, border=2)
    qr_bytes = io.BytesIO()
    qr_image.save(qr_bytes, format="PNG")
    qr_bytes.seek(0)
    qr_size = 78
    qr_x = page_width - 117
    qr_y = 54
    pdf.drawImage(
        ImageReader(qr_bytes),
        qr_x,
        qr_y,
        width=qr_size,
        height=qr_size,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.setFillColor(muted)
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(qr_x + qr_size / 2, qr_y - 10, "Scanner pour vérifier")
    pdf.setFont("Helvetica-Bold", 8)
    pdf.setFillColor(navy)
    pdf.drawString(47, 50, f"Nº {certificate.certificate_number}")
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(muted)
    pdf.drawString(
        47,
        39,
        f"Délivré le {timezone.localtime(certificate.issued_at or timezone.now()).strftime('%d/%m/%Y')}",
    )

    pdf.showPage()
    pdf.save()
    output.seek(0)
    return output.read()


@transaction.atomic
def issue_certificate(certificate, reviewer):
    """Email a PDF only after eligibility, review, signer and mail checks pass."""
    certificate = (
        Certificate.objects.select_for_update()
        .select_related("student", "course")
        .get(pk=certificate.pk)
    )
    if certificate.status not in (
        Certificate.Status.PENDING,
        Certificate.Status.CORRECTION,
    ):
        raise CertificateDeliveryError(
            "Ce certificat a déjà été délivré, révoqué ou n'est pas en attente."
        )
    if not course_is_complete(certificate.student, certificate.course):
        raise CertificateDeliveryError(
            "La progression réelle du cours n'est pas encore à 100 %."
        )
    if not certificate.student.email:
        raise CertificateDeliveryError("L'étudiant n'a pas d'adresse e-mail.")
    if not certificate.signers.filter(is_active=True).exists():
        raise CertificateDeliveryError(
            "Ajoutez au moins un signataire actif avant la délivrance."
        )
    if not getattr(settings, "BREVO_API_KEY", ""):
        raise CertificateDeliveryError(
            "L'envoi réel des e-mails n'est pas configuré (clé Brevo manquante). "
            "Le certificat n'a pas été délivré."
        )

    now = timezone.now()
    verification_url = certificate_verification_url(certificate)
    pdf_bytes = render_certificate_pdf(certificate)
    subject = f"Votre certificat EducaDim — {certificate.course.get_titre()}"
    text_body = (
        f"Bonjour {certificate.student_name},\n\n"
        f"Félicitations : votre réussite au cours "
        f"« {certificate.course.get_titre()} » a été vérifiée par notre équipe.\n"
        "Votre certificat PDF est joint à ce message.\n\n"
        f"Numéro : {certificate.certificate_number}\n"
        f"Vérification en ligne : {verification_url}\n\n"
        f"L'équipe {settings.SITE_NAME}"
    )
    html_body = (
        f"<p>Bonjour {escape(certificate.student_name)},</p>"
        f"<p>Félicitations : votre réussite au cours "
        f"<strong>{escape(certificate.course.get_titre())}</strong> "
        "a été vérifiée par notre équipe. Votre certificat PDF est joint.</p>"
        f"<p>Numéro : <strong>{certificate.certificate_number}</strong><br>"
        f'<a href="{escape(verification_url, quote=True)}">'
        "Vérifier le certificat en ligne</a></p>"
        f"<p>L'équipe {escape(settings.SITE_NAME)}</p>"
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[certificate.student.email],
    )
    email.attach_alternative(html_body, "text/html")
    email.attach(
        f"educadim-certificat-{certificate.certificate_number}.pdf",
        pdf_bytes,
        "application/pdf",
    )
    try:
        sent_count = email.send(fail_silently=False)
    except Exception as exc:
        logger.exception(
            "Certificate email failed certificate=%s",
            certificate.public_id,
        )
        raise CertificateDeliveryError(
            "Le courriel n'a pas pu être envoyé. Le certificat reste en attente."
        ) from exc
    if sent_count != 1:
        raise CertificateDeliveryError(
            "Le fournisseur n'a pas confirmé l'envoi. Le certificat reste en attente."
        )

    certificate.status = Certificate.Status.ISSUED
    certificate.reviewed_by = reviewer
    certificate.reviewed_at = now
    certificate.issued_at = now
    certificate.email_sent_at = now
    certificate.pdf_content = pdf_bytes
    certificate.save(
        update_fields=(
            "status",
            "reviewed_by",
            "reviewed_at",
            "issued_at",
            "email_sent_at",
            "pdf_content",
            "updated_at",
        )
    )
    return certificate
