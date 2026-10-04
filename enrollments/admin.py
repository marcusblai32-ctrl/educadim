from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from .models import Enrollment
from .forms import EnrollmentAdminForm
from notifications.models import Notification
from utils.notifications import notify_safely, send_enrollment_approved, send_enrollment_rejected

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    form = EnrollmentAdminForm
    list_display = ('utilisateur', 'cours', 'statut', 'methode_paiement', 'date_demande')
    list_filter = ('statut', 'methode_paiement', 'cours')
    search_fields = ('utilisateur__email', 'utilisateur__first_name', 'id_transaction')
    readonly_fields = ('date_demande',)

    fieldsets = (
        (None, {'fields': ('utilisateur', 'cours', 'statut', 'methode_paiement')}),
        ('Paiement', {'fields': ('nom_compte', 'telephone', 'id_transaction', 'photo_paiement')}),
        ('Dates', {'fields': ('date_demande', 'date_verification')}),
        ('Administration', {'fields': ('verifie_par', 'note_admin')}),
    )

    actions = ['approuver_inscriptions', 'rejeter_inscriptions']

    def approuver_inscriptions(self, request, queryset):
        count = 0
        for enrollment in queryset:
            if enrollment.statut == 'pending':
                enrollment.statut = 'active'
                enrollment.date_verification = timezone.now()
                enrollment.verifie_par = request.user
                enrollment.save()

                enrollment.delete_photo()

                Notification.objects.create(
                    utilisateur=enrollment.utilisateur,
                    type_notif='systeme',
                    titre="Inscription approuvée",
                    message=f"Votre inscription au cours '{enrollment.cours.titre}' a été approuvée.",
                    lien=f"/cours/{enrollment.cours.pk}/"
                )
                notify_safely(
                    send_enrollment_approved,
                    user=enrollment.utilisateur, enrollment=enrollment,
                    send_email=True, send_sms=bool(enrollment.utilisateur.phone_number),
                )
                count += 1
        messages.success(request, f"{count} inscriptions approuvées.")
    approuver_inscriptions.short_description = "Approuver les inscriptions"

    def rejeter_inscriptions(self, request, queryset):
        count = 0
        for enrollment in queryset:
            if enrollment.statut == 'pending':
                enrollment.statut = 'rejected'
                enrollment.date_verification = timezone.now()
                enrollment.verifie_par = request.user
                enrollment.save()

                enrollment.delete_photo()

                Notification.objects.create(
                    utilisateur=enrollment.utilisateur,
                    type_notif='systeme',
                    titre="Inscription refusée",
                    message=f"Votre inscription au cours '{enrollment.cours.titre}' a été refusée.",
                    lien=f"/cours/{enrollment.cours.pk}/"
                )
                notify_safely(
                    send_enrollment_rejected,
                    user=enrollment.utilisateur, enrollment=enrollment,
                    send_email=True, send_sms=bool(enrollment.utilisateur.phone_number),
                )
                count += 1
        messages.success(request, f"{count} inscriptions refusées.")
    rejeter_inscriptions.short_description = "Refuser les inscriptions"