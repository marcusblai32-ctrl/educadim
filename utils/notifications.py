import logging

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)

try:
    from telerivet import APIClient
except ImportError:
    try:
        from telerivet import Client as APIClient
    except ImportError:
        APIClient = None

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from django.utils import timezone

# ============================================
# BREVO - EMAIL
# ============================================

def send_brevo_email(to_email, subject, template_name, context=None, from_email=None):
    if context is None:
        context = {}

    if not to_email:
        return {'success': False, 'error_code': 'missing_recipient', 'error': 'Recipient email is required.'}

    if not settings.BREVO_API_KEY:
        logger.error("Brevo delivery skipped: BREVO_API_KEY is not configured.")
        return {
            'success': False,
            'error_code': 'brevo_not_configured',
            'error': 'Email delivery is not configured.',
        }

    context.update({
        'site_name': settings.SITE_NAME,
        'site_url': settings.SITE_URL,
    })

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        sender = {
            "email": from_email or settings.BREVO_SENDER_EMAIL,
            "name": settings.BREVO_SENDER_NAME
        }

        recipient = [{"email": to_email}]

        html_content = render_to_string(f'emails/{template_name}', context)
        plain_text = strip_tags(html_content)

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=recipient,
            sender=sender,
            subject=subject,
            html_content=html_content,
            text_content=plain_text
        )

        api_response = api_instance.send_transac_email(send_smtp_email)
        message_id = getattr(api_response, 'message_id', None)
        logger.info("Brevo email delivered template=%s message_id=%s", template_name, message_id)

        return {
            'success': True,
            'message_id': message_id,
            'response': api_response
        }

    except ApiException as e:
        logger.exception("Brevo API delivery failed template=%s status=%s", template_name, getattr(e, 'status', None))
        return {
            'success': False,
            'error_code': 'brevo_api_error',
            'error': 'Email provider rejected the message.',
        }
    except Exception as e:
        logger.exception("Brevo email delivery failed template=%s", template_name)
        return {
            'success': False,
            'error_code': 'brevo_delivery_error',
            'error': 'Email delivery failed.',
        }


# ============================================
# TELERIVET - SMS
# ============================================

def send_telerivet_sms(to_number, message_text):
    if not to_number:
        return {'success': False, 'error_code': 'missing_recipient', 'error': 'Recipient phone number is required.'}

    if not settings.TELERIVET_API_KEY or not settings.TELERIVET_PROJECT_ID:
        logger.error("Telerivet delivery skipped: required settings are not configured.")
        return {
            'success': False,
            'error_code': 'telerivet_not_configured',
            'error': 'SMS delivery is not configured.',
        }

    if APIClient is None:
        logger.error("Telerivet delivery skipped: SDK is not installed.")
        return {
            'success': False,
            'error_code': 'telerivet_sdk_missing',
            'error': 'SMS delivery is unavailable.',
        }

    try:
        client = APIClient(settings.TELERIVET_API_KEY)
        project = client.init_project_by_id(settings.TELERIVET_PROJECT_ID)

        to_number = to_number.strip()
        if not to_number.startswith('+'):
            to_number = '+' + to_number

        result = project.send_message(
            to_number=to_number,
            content=message_text
        )
        message_id = getattr(result, 'id', None)
        logger.info("Telerivet SMS delivered message_id=%s", message_id)

        return {
            'success': True,
            'message_id': message_id,
            'response': result
        }

    except Exception as e:
        logger.exception("Telerivet SMS delivery failed")
        return {
            'success': False,
            'error_code': 'telerivet_delivery_error',
            'error': 'SMS delivery failed.',
        }


# ============================================
# FONKSYON POU JWENN NON ITILIZATÈ
# ============================================

def get_user_full_name(user):
    return user.get_full_name() or user.first_name or user.email

def get_user_first_name(user):
    return user.first_name or user.email.split('@')[0]

def get_user_display_name(user):
    return user.get_full_name() or user.first_name or user.username or user.email


# ============================================
# 1. NOTIFIKASYON POU ENSKRIPSYON (Enrollment)
# ============================================

def send_enrollment_confirmation_email(user, enrollment, course_details=None):
    if course_details is None:
        course_details = {}

    course_name = enrollment.cours.get_titre()
    subject = f"Inscription confirmée - {course_name}"

    context = {
        'user': user,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
        'enrollment': enrollment,
        'course_name': course_name,
        'course_link': course_details.get('course_link', ''),
        'course_slug': enrollment.cours.slug,
        'instructor': enrollment.cours.instructor.get_full_name() if hasattr(enrollment.cours, 'instructor') and enrollment.cours.instructor else 'Notre équipe',
        'start_date': enrollment.cours.start_date.strftime('%d/%m/%Y') if hasattr(enrollment.cours, 'start_date') and enrollment.cours.start_date else 'Immédiat',
        'enrollment_date': enrollment.date_demande.strftime('%d/%m/%Y à %H:%M'),
        'status': enrollment.get_statut_display(),
        'payment_method': enrollment.get_methode_paiement_display(),
        'is_paid': enrollment.methode_paiement not in ['manual', 'subscription'] and enrollment.methode_paiement != '',
    }

    if enrollment.methode_paiement == 'subscription':
        template_name = 'enrollment_subscription.html'
    elif enrollment.methode_paiement in ['moncash', 'natcash']:
        template_name = 'enrollment_paid.html'
    else:
        template_name = 'enrollment_free.html'

    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name=template_name,
        context=context
    )


def send_enrollment_confirmation_sms(user, enrollment):
    first_name = get_user_first_name(user)
    course_name = enrollment.cours.get_titre()

    if enrollment.methode_paiement == 'subscription':
        message = f"{settings.SITE_NAME}: {first_name}, votre abonnement vous donne accès à {course_name}. Bon apprentissage!"
    elif enrollment.methode_paiement in ['moncash', 'natcash']:
        message = f"{settings.SITE_NAME}: {first_name}, inscription confirmée pour {course_name}. Paiement reçu. Merci!"
    else:
        message = f"{settings.SITE_NAME}: {first_name}, inscription confirmée pour {course_name}. Bon apprentissage!"

    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=message
    )


def send_enrollment_confirmation(user, enrollment, course_details=None, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_enrollment_confirmation_email(user, enrollment, course_details)

    if send_sms and user.phone_number:
        results['sms'] = send_enrollment_confirmation_sms(user, enrollment)

    return results


# ============================================
# 2. NOTIFIKASYON POU APROBA ENSKRIPSYON
# ============================================

def send_enrollment_approved_email(user, enrollment, admin_note=None):
    course_name = enrollment.cours.get_titre()
    subject = f"Inscription approuvée - {course_name}"

    context = {
        'user': user,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
        'enrollment': enrollment,
        'course_name': course_name,
        'course_link': '',
        'instructor': enrollment.cours.instructor.get_full_name() if hasattr(enrollment.cours, 'instructor') and enrollment.cours.instructor else 'Notre équipe',
        'start_date': enrollment.cours.start_date.strftime('%d/%m/%Y') if hasattr(enrollment.cours, 'start_date') and enrollment.cours.start_date else 'Immédiat',
        'enrollment_date': enrollment.date_demande.strftime('%d/%m/%Y à %H:%M'),
        'verification_date': enrollment.date_verification.strftime('%d/%m/%Y à %H:%M') if enrollment.date_verification else '',
        'verified_by': enrollment.verifie_par.get_full_name() if enrollment.verifie_par else 'Admin',
        'admin_note': admin_note or enrollment.note_admin,
        'payment_method': enrollment.get_methode_paiement_display(),
        'is_paid': enrollment.methode_paiement not in ['manual', 'subscription'] and enrollment.methode_paiement != '',
    }

    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name='enrollment_approved.html',
        context=context
    )


def send_enrollment_approved_sms(user, enrollment):
    first_name = get_user_first_name(user)
    course_name = enrollment.cours.get_titre()
    message = f"{settings.SITE_NAME}: {first_name}, votre inscription pour {course_name} a été approuvée. Accédez au cours maintenant!"
    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=message
    )


def send_enrollment_approved(user, enrollment, admin_note=None, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_enrollment_approved_email(user, enrollment, admin_note)

    if send_sms and user.phone_number:
        results['sms'] = send_enrollment_approved_sms(user, enrollment)

    return results


# ============================================
# 3. NOTIFIKASYON POU REJEKSYON ENSKRIPSYON
# ============================================

def send_enrollment_rejected_email(user, enrollment, admin_note=None):
    course_name = enrollment.cours.get_titre()
    subject = f"Inscription refusée - {course_name}"

    context = {
        'user': user,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
        'enrollment': enrollment,
        'course_name': course_name,
        'enrollment_date': enrollment.date_demande.strftime('%d/%m/%Y à %H:%M'),
        'verification_date': enrollment.date_verification.strftime('%d/%m/%Y à %H:%M') if enrollment.date_verification else '',
        'verified_by': enrollment.verifie_par.get_full_name() if enrollment.verifie_par else 'Admin',
        'admin_note': admin_note or enrollment.note_admin or 'Veuillez vérifier vos informations et réessayer.',
        'payment_method': enrollment.get_methode_paiement_display(),
    }

    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name='enrollment_rejected.html',
        context=context
    )


def send_enrollment_rejected_sms(user, enrollment):
    first_name = get_user_first_name(user)
    course_name = enrollment.cours.get_titre()
    message = f"{settings.SITE_NAME}: {first_name}, votre inscription pour {course_name} a été refusée. Consultez vos emails pour plus d'informations."
    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=message
    )


def send_enrollment_rejected(user, enrollment, admin_note=None, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_enrollment_rejected_email(user, enrollment, admin_note)

    if send_sms and user.phone_number:
        results['sms'] = send_enrollment_rejected_sms(user, enrollment)

    return results


# ============================================
# 4. NOTIFIKASYON POU ABONNMAN (Subscription)
# ============================================

def send_subscription_confirmation_email(user, subscription):
    subject = f"Abonnement confirmé - {subscription.plan.nom}"

    context = {
        'user': user,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
        'subscription': subscription,
        'plan_name': subscription.plan.nom,
        'plan_description': subscription.plan.description,
        'plan_price': subscription.plan.prix,
        'plan_duration': subscription.plan.duree_jours,
        'start_date': subscription.date_debut.strftime('%d/%m/%Y') if subscription.date_debut else 'En attente',
        'end_date': subscription.date_fin.strftime('%d/%m/%Y') if subscription.date_fin else 'Non spécifiée',
        'status': subscription.get_statut_display(),
        'payment_method': subscription.get_methode_paiement_display(),
        'courses': subscription.plan.cours.all(),
    }

    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name='subscription_confirmed.html',
        context=context
    )


def send_subscription_confirmation_sms(user, subscription):
    first_name = get_user_first_name(user)
    plan_name = subscription.plan.nom
    message = f"{settings.SITE_NAME}: {first_name}, votre abonnement {plan_name} est confirmé. Profitez de vos cours!"
    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=message
    )


def send_subscription_confirmation(user, subscription, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_subscription_confirmation_email(user, subscription)

    if send_sms and user.phone_number:
        results['sms'] = send_subscription_confirmation_sms(user, subscription)

    return results


# ============================================
# 5. NOTIFIKASYON POU APROBA ABONNMAN
# ============================================

def send_subscription_approved_email(user, subscription, admin_note=None):
    subject = f"Abonnement approuvé - {subscription.plan.nom}"

    context = {
        'user': user,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
        'subscription': subscription,
        'plan_name': subscription.plan.nom,
        'plan_description': subscription.plan.description,
        'plan_price': subscription.plan.prix,
        'plan_duration': subscription.plan.duree_jours,
        'start_date': subscription.date_debut.strftime('%d/%m/%Y') if subscription.date_debut else 'Aujourd\'hui',
        'end_date': subscription.date_fin.strftime('%d/%m/%Y') if subscription.date_fin else 'Non spécifiée',
        'status': subscription.get_statut_display(),
        'payment_method': subscription.get_methode_paiement_display(),
        'verification_date': subscription.date_verification.strftime('%d/%m/%Y à %H:%M') if subscription.date_verification else '',
        'verified_by': subscription.verifie_par.get_full_name() if subscription.verifie_par else 'Admin',
        'admin_note': admin_note or subscription.note_admin,
        'courses': subscription.plan.cours.all(),
    }

    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name='subscription_approved.html',
        context=context
    )


def send_subscription_approved_sms(user, subscription):
    first_name = get_user_first_name(user)
    plan_name = subscription.plan.nom
    message = f"{settings.SITE_NAME}: {first_name}, votre abonnement {plan_name} a été approuvé. Commencez à apprendre!"
    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=message
    )


def send_subscription_approved(user, subscription, admin_note=None, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_subscription_approved_email(user, subscription, admin_note)

    if send_sms and user.phone_number:
        results['sms'] = send_subscription_approved_sms(user, subscription)

    return results


# ============================================
# 6. REYINISYALIZE MODPAS
# ============================================

def send_password_reset_email(user, reset_link):
    subject = f"Réinitialisation de votre mot de passe - {settings.SITE_NAME}"
    context = {
        'user': user,
        'reset_link': reset_link,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
    }
    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name='password_reset.html',
        context=context
    )


def send_password_reset_sms(user, reset_link):
    first_name = get_user_first_name(user)
    message = f"{settings.SITE_NAME}: {first_name}, réinitialisez votre mot de passe ici: {reset_link}"
    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=message
    )


def send_password_reset(user, reset_link, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_password_reset_email(user, reset_link)

    if send_sms and user.phone_number:
        results['sms'] = send_password_reset_sms(user, reset_link)

    return results


# ============================================
# 7. NOTIFIKASYON JENERAL
# ============================================

def send_notification_email(user, subject, message, link=None):
    context = {
        'user': user,
        'first_name': get_user_first_name(user),
        'full_name': get_user_full_name(user),
        'email': user.email,
        'username': user.email,
        'user_id': user.user_id,
        'message': message,
        'link': link,
    }
    return send_brevo_email(
        to_email=user.email,
        subject=subject,
        template_name='notification.html',
        context=context
    )


def send_notification_sms(user, message):
    first_name = get_user_first_name(user)
    sms_message = f"{settings.SITE_NAME}: {first_name}, {message}"
    return send_telerivet_sms(
        to_number=user.phone_number,
        message_text=sms_message
    )


def send_notification(user, subject, message, link=None, send_email=True, send_sms=False):
    results = {}

    if send_email and user.email:
        results['email'] = send_notification_email(user, subject, message, link)

    if send_sms and user.phone_number:
        results['sms'] = send_notification_sms(user, message)

    return results