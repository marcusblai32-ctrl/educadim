from django.contrib import admin
from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from .models import SubscriptionPlan, Subscription, SubscriptionAccess, SubscriptionCourseSelection
from utils.notifications import notify_safely, send_subscription_approved
from notifications.models import Notification


class SubscriptionAccessInline(admin.TabularInline):
    model = SubscriptionAccess
    extra = 0
    readonly_fields = ('date_acces', 'date_expiration')
    can_delete = False


class SubscriptionCourseSelectionInline(admin.TabularInline):
    """NOUVO: Montre seleksyon kou yo nan admin Subscription."""
    model = SubscriptionCourseSelection
    extra = 0
    readonly_fields = ('date_selection',)
    can_delete = True
    verbose_name = "Cours sélectionné"
    verbose_name_plural = "Cours sélectionnés"


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'duree_jours', 'max_courses', 'actif', 'get_courses_count')
    list_filter = ('actif',)
    search_fields = ('nom', 'description')
    filter_horizontal = ('cours',)
    fieldsets = (
        (None, {'fields': ('nom', 'description', 'prix', 'duree_jours', 'actif')}),
        ('Cours inclus', {'fields': ('cours',)}),
        # ===== NOUVO FIELDSET =====
        ('Limites', {
            'fields': ('max_courses',),
            'description': '0 = tous les cours du plan (ancien comportement). Sinon, limite le nombre de cours.'
        }),
    )

    def get_courses_count(self, obj):
        """Montre kantite kou nan plan an."""
        return obj.cours.count()
    get_courses_count.short_description = _("Nb cours")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'plan', 'statut', 'methode_paiement', 'date_demande', 'est_actif', 'courses_selectionnes')
    list_filter = ('statut', 'methode_paiement', 'plan', 'courses_selectionnes')
    search_fields = ('utilisateur__email', 'utilisateur__first_name', 'id_transaction')
    readonly_fields = ('date_demande',)
    inlines = [SubscriptionAccessInline, SubscriptionCourseSelectionInline]

    fieldsets = (
        ('Informations générales', {
            'fields': ('utilisateur', 'plan', 'statut', 'methode_paiement', 'courses_selectionnes')
        }),
        ('Paiement', {
            'fields': ('nom_compte', 'telephone', 'id_transaction', 'photo_paiement')
        }),
        ('Dates', {
            'fields': ('date_demande', 'date_debut', 'date_fin', 'date_verification')
        }),
        ('Administration', {
            'fields': ('verifie_par', 'note_admin')
        }),
    )

    actions = ['approuver_paiement', 'rejeter_paiement', 'reactiver_acces']

    # ===== MODIFIE: approuver_paiement =====
    def approuver_paiement(self, request, queryset):
        """Apwouve peman epi kreye aksè selon nouvo workflow."""
        count = 0
        redirections = 0
        
        for sub in queryset:
            if sub.statut == 'pending':
                sub.statut = 'active'
                sub.date_debut = timezone.now()
                sub.date_fin = timezone.now() + timezone.timedelta(days=sub.plan.duree_jours)
                sub.date_verification = timezone.now()
                sub.verifie_par = request.user
                sub.save()

                sub.delete_photo()

                # ===== NOUVO WORKFLOW: Si max_courses > 0 =====
                if sub.plan.max_courses > 0:
                    # Pa kreye aksè kounya - itilizatè a dwe chwazi kou yo
                    Notification.objects.create(
                        utilisateur=sub.utilisateur,
                        type_notif='systeme',
                        titre="Abonnement approuvé - Choisissez vos cours",
                        message=f"Votre abonnement '{sub.plan.nom}' a été approuvé. Vous pouvez maintenant choisir jusqu'à {sub.plan.max_courses} cours.",
                        lien=f"/abonnements/chwazi-kou/{sub.pk}/"
                    )
                    redirections += 1
                    notify_safely(send_subscription_approved, user=sub.utilisateur, subscription=sub,
                                  send_email=True, send_sms=bool(sub.utilisateur.phone_number))
                else:
                    # ===== ANSYEN WORKFLOW: max_courses == 0 =====
                    # Kreye aksè pou tout kou plan an
                    for cours in sub.plan.cours.all():
                        SubscriptionAccess.objects.get_or_create(
                            subscription=sub,
                            cours=cours,
                            defaults={'date_expiration': sub.date_fin}
                        )
                    
                    sub.courses_selectionnes = True
                    sub.save(update_fields=['courses_selectionnes'])
                    
                    Notification.objects.create(
                        utilisateur=sub.utilisateur,
                        type_notif='systeme',
                        titre="Abonnement approuvé",
                        message=f"Votre abonnement '{sub.plan.nom}' a été approuvé. Tous les cours sont maintenant accessibles.",
                        lien="/abonnements/mes-abonnements/"
                    )
                    notify_safely(send_subscription_approved, user=sub.utilisateur, subscription=sub,
                                  send_email=True, send_sms=bool(sub.utilisateur.phone_number))
                
                count += 1
        
        if redirections > 0:
            messages.success(
                request,
                f"{count} abonnements approuvés. {redirections} nécessitent une sélection de cours."
            )
        else:
            messages.success(request, f"{count} abonnements approuvés.")

    approuver_paiement.short_description = _("Approuver le paiement")

    # ===== ANSYEN: rejeter_paiement (PA TOUCHE) =====
    def rejeter_paiement(self, request, queryset):
        count = 0
        for sub in queryset:
            if sub.statut == 'pending':
                sub.statut = 'rejected'
                sub.date_verification = timezone.now()
                sub.verifie_par = request.user
                sub.save()

                sub.delete_photo()

                Notification.objects.create(
                    utilisateur=sub.utilisateur,
                    type_notif='systeme',
                    titre="Abonnement refusé",
                    message=f"Votre abonnement '{sub.plan.nom}' a été refusé.",
                    lien="/abonnements/mes-abonnements/"
                )
                count += 1
        messages.success(request, f"{count} abonnements rejetés.")

    rejeter_paiement.short_description = _("Rejeter le paiement")

    # ===== NOUVO ACTION: Réactiver les accès =====
    def reactiver_acces(self, request, queryset):
        """Réactive les accès pour les abonnements actifs."""
        count = 0
        for sub in queryset:
            if sub.statut == 'active' and sub.date_fin and sub.date_fin > timezone.now():
                # Kreye/aktyalize aksè yo
                for cours in sub.plan.cours.all():
                    SubscriptionAccess.objects.update_or_create(
                        subscription=sub,
                        cours=cours,
                        defaults={'date_expiration': sub.date_fin}
                    )
                count += 1
        
        messages.success(request, f"{count} abonnements réactivés.")

    reactiver_acces.short_description = _("Réactiver les accès")


@admin.register(SubscriptionAccess)
class SubscriptionAccessAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'cours', 'date_acces', 'date_expiration')
    list_filter = ('date_acces', 'date_expiration')
    search_fields = ('subscription__utilisateur__email', 'cours__titre')
    readonly_fields = ('date_acces',)
    
    def est_actif(self, obj):
        """Montre si aksè a toujou valab."""
        if obj.date_expiration:
            return obj.date_expiration > timezone.now()
        return False
    est_actif.boolean = True
    est_actif.short_description = _("Actif")


# ===== NOUVO MODEL ADMIN =====
@admin.register(SubscriptionCourseSelection)
class SubscriptionCourseSelectionAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'course', 'date_selection')
    list_filter = ('date_selection',)
    search_fields = ('subscription__utilisateur__email', 'course__titre')
    readonly_fields = ('date_selection',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'subscription__utilisateur',
            'course'
        )