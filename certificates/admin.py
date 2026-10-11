from django.contrib import admin

from .models import Certificate, CertificateSigner


@admin.register(CertificateSigner)
class CertificateSignerAdmin(admin.ModelAdmin):
    list_display = ("name", "title", "order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "title")
    ordering = ("order", "name")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = (
        "certificate_number",
        "student_name",
        "course",
        "status",
        "created_at",
        "email_sent_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "student_name",
        "student__email",
        "course__titre",
        "public_id",
    )
    readonly_fields = (
        "public_id",
        "student",
        "course",
        "student_name",
        "completed_at",
        "status",
        "signers",
        "student_note",
        "review_note",
        "pdf_content",
        "reviewed_by",
        "reviewed_at",
        "issued_at",
        "email_sent_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
