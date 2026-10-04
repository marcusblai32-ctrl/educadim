from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.utils import timezone
from django.urls import reverse
from django.conf import settings

from .models import Notification
from enrollments.models import Enrollment
from subscriptions.models import Subscription
from courses.models import Course
from accounts.models import CustomUser

from utils.notifications import (
    send_enrollment_confirmation,
    send_enrollment_approved,
    send_enrollment_rejected,
    send_subscription_confirmation,
    send_subscription_approved,
    send_password_reset,
    send_notification,
    send_brevo_email,
    send_telerivet_sms
)


# ============================================
# ANCIENNES VIEW
# ============================================

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(utilisateur=request.user)
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_read_ajax(request, pk):
    notif = get_object_or_404(Notification, pk=pk, utilisateur=request.user)
    notif.lue = True
    notif.save()
    return JsonResponse({'status': 'ok'})

@login_required
def delete_notification(request, pk):
    notif = get_object_or_404(Notification, pk=pk, utilisateur=request.user)
    notif.delete()
    messages.success(request, _("Notification supprimée."))
    return redirect('notifications:list')

@login_required
def delete_all_notifications(request):
    Notification.objects.filter(utilisateur=request.user).delete()
    messages.success(request, _("Toutes les notifications ont été supprimées."))
    return redirect('notifications:list')

@login_required
def get_unread_count(request):
    count = Notification.objects.filter(utilisateur=request.user, lue=False).count()
    return JsonResponse({'count': count})


# ============================================
# NOUVEAU VIEW
# ============================================

@login_required
def enroll_free_course(request, course_id):
    course = get_object_or_404(Course, id=course_id, prix=0, publie=True)

    if Enrollment.objects.filter(utilisateur=request.user, cours=course).exists():
        messages.warning(request, f"Ou deja enskri nan {course.titre}.")
        return redirect('courses:course_detail', pk=course.pk)

    enrollment = Enrollment.objects.create(
        utilisateur=request.user,
        cours=course,
        statut='active',
        methode_paiement='manual',
        date_demande=timezone.now()
    )

    course_details = {
        'course_link': request.build_absolute_uri(reverse('courses:course_detail', args=[course.pk]))
    }

    result = send_enrollment_confirmation(
        user=request.user,
        enrollment=enrollment,
        course_details=course_details,
        send_email=True,
        send_sms=True
    )

    messages.success(request, f"Félicitations! Vous êtes inscrit au cours {course.titre}.")
    return redirect('courses:course_detail', pk=course.pk)


@staff_member_required
def approve_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    if enrollment.statut == 'active':
        messages.warning(request, "Enskripsyon sa deja aktif.")
        return redirect('admin:enrollments_enrollment_changelist')

    enrollment.statut = 'active'
    enrollment.verifie_par = request.user
    enrollment.date_verification = timezone.now()
    enrollment.save()

    result = send_enrollment_approved(
        user=enrollment.utilisateur,
        enrollment=enrollment,
        admin_note="Votre inscription a été approuvée. Bienvenue!",
        send_email=True,
        send_sms=True
    )

    messages.success(request, f"Inscription de {enrollment.utilisateur.get_full_name()} approuvée.")
    return redirect('admin:enrollments_enrollment_changelist')


@staff_member_required
def reject_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)

    if enrollment.statut == 'rejected':
        messages.warning(request, "Enskripsyon sa deja refize.")
        return redirect('admin:enrollments_enrollment_changelist')

    enrollment.statut = 'rejected'
    enrollment.verifie_par = request.user
    enrollment.date_verification = timezone.now()
    enrollment.save()

    result = send_enrollment_rejected(
        user=enrollment.utilisateur,
        enrollment=enrollment,
        admin_note="Veuillez vérifier votre photo de paiement et réessayer.",
        send_email=True,
        send_sms=True
    )

    messages.warning(request, f"Inscription de {enrollment.utilisateur.get_full_name()} refusée.")
    return redirect('admin:enrollments_enrollment_changelist')


@login_required
def confirm_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id, utilisateur=request.user)

    if subscription.statut == 'active':
        messages.warning(request, "Abonman sa deja aktif.")
        return redirect('subscriptions:my_subscriptions')

    subscription.statut = 'active'
    subscription.date_debut = timezone.now()
    subscription.date_fin = timezone.now() + timezone.timedelta(days=subscription.plan.duree_jours)
    subscription.save()

    result = send_subscription_confirmation(
        user=request.user,
        subscription=subscription,
        send_email=True,
        send_sms=True
    )

    messages.success(request, f"Abonnement {subscription.plan.nom} confirmé!")
    return redirect('subscriptions:my_subscriptions')


@staff_member_required
def approve_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id)

    if subscription.statut == 'active':
        messages.warning(request, "Abonman sa deja aktif.")
        return redirect('admin:subscriptions_subscription_changelist')

    subscription.statut = 'active'
    subscription.date_debut = timezone.now()
    subscription.date_fin = timezone.now() + timezone.timedelta(days=subscription.plan.duree_jours)
    subscription.verifie_par = request.user
    subscription.date_verification = timezone.now()
    subscription.save()

    result = send_subscription_approved(
        user=subscription.utilisateur,
        subscription=subscription,
        admin_note="Votre abonnement a été approuvé. Profitez de vos cours!",
        send_email=True,
        send_sms=True
    )

    messages.success(request, f"Abonnement de {subscription.utilisateur.get_full_name()} approuvé.")
    return redirect('admin:subscriptions_subscription_changelist')


def password_reset_request(request):
    """Ansyen wout: voye sou vrè sistèm reyinisyalizasyon Django a (token valid, pa gen lyen fo)."""
    return redirect('accounts:password_reset')


@staff_member_required
def test_notification(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', 'Test Notifikasyon')
        message = request.POST.get('message', 'Sa se yon tès notifikasyon')
        send_email = request.POST.get('send_email', 'on') == 'on'
        send_sms = request.POST.get('send_sms', 'off') == 'on'

        result = send_notification(
            user=request.user,
            subject=subject,
            message=message,
            link=settings.SITE_URL,
            send_email=send_email,
            send_sms=send_sms
        )

        if result.get('email', {}).get('success') or result.get('sms', {}).get('success'):
            messages.success(request, "Notifikasyon voye avèk siksè!")
        else:
            messages.error(request, f"Erè: {result}")

        return redirect('notifications:test')

    return render(request, 'notifications/test.html')


@staff_member_required
def test_email(request):
    if request.method == 'POST':
        to_email = request.POST.get('to_email', request.user.email)
        subject = request.POST.get('subject', 'Test Email - EducDim')
        message = request.POST.get('message', 'Sa se yon tès imel ki soti nan EducDim!')

        context = {
            'first_name': request.user.first_name or request.user.email,
            'message': message,
            'user': request.user,
            'full_name': request.user.get_full_name() or request.user.email,
            'email': request.user.email,
            'username': request.user.email,
        }

        result = send_brevo_email(
            to_email=to_email,
            subject=subject,
            template_name='test_email.html',
            context=context
        )

        if result.get('success'):
            messages.success(request, f"Email voye avèk siksè a {to_email}!")
        else:
            messages.error(request, f"Erè: {result.get('error')}")

        return redirect('notifications:test_email')

    return render(request, 'notifications/test_email.html')


@staff_member_required
def test_sms(request):
    if request.method == 'POST':
        to_number = request.POST.get('to_number', request.user.phone_number)
        message = request.POST.get('message', 'EducDim: Sa se yon tès SMS. Konfigirasyon an byen mache!')

        if not to_number:
            messages.error(request, "Ou pa gen nimewo telefòn. Ajoute yon nimewo nan profil ou.")
            return redirect('notifications:test_sms')

        result = send_telerivet_sms(
            to_number=to_number,
            message_text=message
        )

        if result.get('success'):
            messages.success(request, f"SMS voye avèk siksè a {to_number}!")
        else:
            messages.error(request, f"Erè: {result.get('error')}")

        return redirect('notifications:test_sms')

    return render(request, 'notifications/test_sms.html')