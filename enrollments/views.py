from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.utils.translation import gettext as _
from .models import Enrollment
from .forms import EnrollmentPaymentForm, EnrollmentAdminForm
from courses.models import Course
from notifications.models import Notification
from utils.notifications import notify_safely, send_enrollment_approved, send_enrollment_rejected
from subscriptions.models import SubscriptionAccess, Subscription
import os


@login_required
def enrollment_list(request):
    inscriptions = Enrollment.objects.filter(utilisateur=request.user).select_related('cours')
    return render(request, 'enrollments/enrollment_list.html', {'inscriptions': inscriptions})


@login_required
def enrollment_detail(request, pk):
    inscription = get_object_or_404(Enrollment, pk=pk)
    if inscription.utilisateur != request.user and not request.user.is_staff:
        raise PermissionDenied(_("Vous n'avez pas accès à cette inscription."))
    return render(request, 'enrollments/enrollment_detail.html', {'inscription': inscription})


@login_required
def enroll_course(request, cours_pk):
    cours = get_object_or_404(Course, pk=cours_pk)

    # ===== 1. Tcheke si deja enskri =====
    existing = Enrollment.objects.filter(
        utilisateur=request.user,
        cours=cours,
        statut='active'
    ).first()
    if existing:
        messages.info(request, _("Vous êtes déjà inscrit à ce cours."))
        return redirect('courses:course_detail', pk=cours.pk)

    # ===== 2. Tcheke si abònman aktif bay aksè =====
    has_subscription_access = SubscriptionAccess.objects.filter(
        subscription__utilisateur=request.user,
        subscription__statut='active',
        cours=cours,
        date_expiration__gt=timezone.now()
    ).exists()

    if has_subscription_access:
        # Enskripsyon otomatik atravè abònman
        enrollment = Enrollment.objects.get_or_create(
            utilisateur=request.user,
            cours=cours,
            defaults={
                'statut': 'active',
                'methode_paiement': 'subscription',
                'note_admin': "Accès via abonnement"
            }
        )
        messages.success(request, _("Inscription réussie via votre abonnement !"))
        return redirect('courses:course_detail', pk=cours.pk)

    # ===== 3. Tcheke abònman san limit (max_courses=0) =====
    abonnement_san_limit = Subscription.objects.filter(
        utilisateur=request.user,
        statut='active',
        plan__max_courses=0,
        plan__cours=cours,
        date_fin__gt=timezone.now()
    ).first()

    if abonnement_san_limit:
        # Kreye aksè otomatikman
        SubscriptionAccess.objects.get_or_create(
            subscription=abonnement_san_limit,
            cours=cours,
            defaults={'date_expiration': abonnement_san_limit.date_fin}
        )
        # Enskripsyon otomatik tou
        Enrollment.objects.get_or_create(
            utilisateur=request.user,
            cours=cours,
            defaults={
                'statut': 'active',
                'methode_paiement': 'subscription',
                'note_admin': f"Accès via abonnement {abonnement_san_limit.plan.nom}"
            }
        )
        messages.success(request, _("Votre abonnement vous donne accès à ce cours !"))
        return redirect('courses:course_detail', pk=cours.pk)

    # ===== 4. Kou gratis → enskripsyon otomatik =====
    if not cours.est_payant:
        enrollment = Enrollment.objects.create(
            utilisateur=request.user,
            cours=cours,
            statut='active',
            methode_paiement='manual',
            note_admin="Cours gratuit - accès direct"
        )
        messages.success(request, _("Inscription réussie au cours '{}'.").format(cours.titre))
        return redirect('courses:course_detail', pk=cours.pk)

    # ===== 5. Kou peyan → montre fòmilè peman =====
    if request.method == 'POST':
        form = EnrollmentPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.utilisateur = request.user
            enrollment.cours = cours
            enrollment.statut = 'pending'
            enrollment.save()

            # Notifye admin yo
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admins = User.objects.filter(is_staff=True)
            for admin in admins:
                Notification.objects.create(
                    utilisateur=admin,
                    type_notif='systeme',
                    titre="Nouvelle demande d'inscription",
                    message=f"{request.user.get_full_name()} demande l'inscription au cours '{cours.titre}'.",
                    lien=f"/dp/enrollments/enrollment/{enrollment.pk}/change/"
                )

            messages.success(request, _("Votre demande a été envoyée. Un administrateur vérifiera votre paiement."))
            return redirect('courses:course_detail', pk=cours.pk)
    else:
        form = EnrollmentPaymentForm()

    return render(request, 'enrollments/enroll_form.html', {'form': form, 'cours': cours})


@user_passes_test(lambda u: u.is_staff)
def admin_pending(request):
    inscriptions = Enrollment.objects.filter(statut='pending').select_related('utilisateur', 'cours')
    return render(request, 'enrollments/admin_pending.html', {'inscriptions': inscriptions})


@user_passes_test(lambda u: u.is_staff)
def admin_approve_enrollment(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
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
        messages.success(request, f"Inscription de {enrollment.utilisateur.get_full_name()} approuvée.")
    return redirect('enrollments:admin_pending')


@user_passes_test(lambda u: u.is_staff)
def admin_reject_enrollment(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
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
        messages.success(request, f"Inscription de {enrollment.utilisateur.get_full_name()} refusée.")
    return redirect('enrollments:admin_pending')