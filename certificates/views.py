from functools import wraps
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from progress.models import ProgresCours

from .forms import (
    CertificateRequestForm,
    CertificateReviewForm,
    CertificateRevokeForm,
)
from .models import Certificate
from .services import (
    CertificateDeliveryError,
    course_is_complete,
    issue_certificate,
    render_certificate_pdf,
)


def staff_required(view):
    @wraps(view)
    @login_required
    def wrapped(request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)

    return wrapped


def _sync_completed_certificates():
    """Backfill eligible course completions made before certificates were added."""
    for progress in (
        ProgresCours.objects.filter(pourcentage__gte=100)
        .select_related("utilisateur", "cours")
        .iterator()
    ):
        Certificate.objects.get_or_create(
            student=progress.utilisateur,
            course=progress.cours,
            defaults={
                "student_name": (
                    progress.utilisateur.get_full_name()
                    or progress.utilisateur.email
                ),
                "completed_at": progress.date_modification,
            },
        )


@login_required
def my_certificates(request):
    _sync_completed_certificates()
    certificates = (
        Certificate.objects.filter(student=request.user)
        .select_related("course")
        .prefetch_related("signers")
    )
    return render(
        request,
        "certificates/mine.html",
        {"certificates": certificates},
    )


@login_required
@require_POST
def submit_certificate_details(request, public_id):
    certificate = get_object_or_404(
        Certificate,
        public_id=public_id,
        student=request.user,
    )
    if certificate.status not in (
        Certificate.Status.PENDING,
        Certificate.Status.CORRECTION,
    ):
        messages.error(request, "Ce certificat n'est plus modifiable.")
        return redirect("certificates:mine")

    form = CertificateRequestForm(request.POST, instance=certificate)
    if form.is_valid():
        certificate = form.save(commit=False)
        certificate.status = Certificate.Status.PENDING
        certificate.reviewed_by = None
        certificate.reviewed_at = None
        certificate.save()
        messages.success(
            request,
            "Les informations ont été envoyées à l'équipe pour vérification.",
        )
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                messages.error(request, error)
    return redirect("certificates:mine")


@staff_required
def review_queue(request):
    _sync_completed_certificates()
    selected_status = request.GET.get("status", "pending")
    valid_statuses = {choice[0] for choice in Certificate.Status.choices}
    if selected_status not in valid_statuses:
        selected_status = "pending"
    certificates = (
        Certificate.objects.filter(status=selected_status)
        .select_related("student", "course")
        .order_by("created_at")
    )
    return render(
        request,
        "certificates/review_queue.html",
        {
            "certificates": certificates,
            "selected_status": selected_status,
            "statuses": Certificate.Status.choices,
        },
    )


@staff_required
def review_certificate(request, public_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related("student", "course").prefetch_related(
            "signers"
        ),
        public_id=public_id,
    )

    if certificate.status == Certificate.Status.ISSUED:
        form = CertificateRevokeForm()
        if request.method == "POST":
            form = CertificateRevokeForm(request.POST)
            if form.is_valid():
                certificate.status = Certificate.Status.REVOKED
                certificate.review_note = form.cleaned_data["review_note"]
                certificate.reviewed_by = request.user
                certificate.reviewed_at = timezone.now()
                certificate.save(
                    update_fields=(
                        "status",
                        "review_note",
                        "reviewed_by",
                        "reviewed_at",
                        "updated_at",
                    )
                )
                messages.success(request, "Le certificat a été révoqué.")
                return redirect("certificates:review_queue")
        return render(
            request,
            "certificates/review_detail.html",
            {"certificate": certificate, "revoke_form": form},
        )

    if certificate.status == Certificate.Status.REVOKED:
        messages.info(request, "Ce certificat est déjà révoqué.")
        return redirect("certificates:review_queue")

    form = CertificateReviewForm(
        request.POST or None,
        initial={
            "student_name": certificate.student_name,
            "review_note": certificate.review_note,
            "signers": certificate.signers.filter(is_active=True),
        },
    )
    if request.method == "POST" and form.is_valid():
        certificate.student_name = form.cleaned_data["student_name"].strip()
        certificate.review_note = form.cleaned_data["review_note"].strip()

        if form.cleaned_data["decision"] == "correction":
            certificate.status = Certificate.Status.CORRECTION
            certificate.reviewed_by = request.user
            certificate.reviewed_at = timezone.now()
            certificate.signers.set(form.cleaned_data["signers"])
            certificate.save()
            messages.info(
                request,
                "La correction a été demandée; aucun PDF n'a été envoyé.",
            )
            return redirect("certificates:review_queue")

        if not course_is_complete(certificate.student, certificate.course):
            form.add_error(
                None,
                "La progression réelle du cours n'est pas à 100 %. "
                "Le certificat ne peut pas être délivré.",
            )
        else:
            certificate.signers.set(form.cleaned_data["signers"])
            certificate.save()
            try:
                issue_certificate(certificate, request.user)
            except CertificateDeliveryError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request,
                    f"Certificat délivré et envoyé à {certificate.student.email}.",
                )
                return redirect("certificates:review_queue")

    return render(
        request,
        "certificates/review_detail.html",
        {"certificate": certificate, "form": form},
    )


@login_required
def download_certificate(request, public_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related("student", "course").prefetch_related(
            "signers"
        ),
        public_id=public_id,
        status=Certificate.Status.ISSUED,
    )
    if not request.user.is_staff and certificate.student_id != request.user.pk:
        raise Http404
    if not certificate.pdf_content:
        raise Http404
    pdf_bytes = bytes(certificate.pdf_content)
    filename = f"educadim-certificat-{certificate.certificate_number}.pdf"
    response = FileResponse(
        BytesIO(pdf_bytes),
        as_attachment=True,
        filename=filename,
        content_type="application/pdf",
    )
    response["Cache-Control"] = "private, no-store"
    return response


def verify_certificate(request, public_id):
    certificate = get_object_or_404(
        Certificate.objects.select_related("course"),
        public_id=public_id,
        status__in=(Certificate.Status.ISSUED, Certificate.Status.REVOKED),
    )
    response = render(
        request,
        "certificates/verify.html",
        {
            "certificate": certificate,
            "is_valid": certificate.status == Certificate.Status.ISSUED,
        },
    )
    response["Cache-Control"] = "no-store"
    return response
