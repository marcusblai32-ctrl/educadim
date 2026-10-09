import logging

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

try:
    from telerivet import API as APIClient
except ImportError:
    APIClient = None


# ============================================
# BREVO - EMAIL
# ============================================

def send_brevo_email(
    to_email,
    subject,
    template_name,
    context=None,
    from_email=None,
):
    if context is None:
        context = {}

    if not to_email:
        return {
            'success': False,
            'error_code': 'missing_recipient',
            'error': 'Recipient email is required.',
        }

    if not settings.BREVO_API_KEY:
        logger.error(
            "Brevo delivery skipped: BREVO_API_KEY is not configured."
        )
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
            'email': from_email or settings.BREVO_SENDER_EMAIL,
            'name': settings.BREVO_SENDER_NAME,
        }

        recipient = [{'email': to_email}]

        # Chaje modèl HTML la depi templates/emails/
        html_content = render_to_string(
            f'emails/{template_name}',
            context,
        )

        # Kreye yon vèsyon tèks senp pou kliyan imèl ki pa montre HTML.
        plain_text = strip_tags(html_content)

        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=recipient,
            sender=sender,
            subject=subject,
            html_content=html_content,
            text_content=plain_text,
        )

        api_response = api_instance.send_transac_email(
            send_smtp_email
        )

        message_id = getattr(api_response, 'message_id', None)

        logger.info(
            "Brevo email submitted template=%s message_id=%s",
            template_name,
            message_id,
        )

        return {
            'success': True,
            'message_id': message_id,
            'response': api_response,
        }

    except ApiException as e:
        logger.exception(
            "Brevo API delivery failed template=%s status=%s",
            template_name,
            getattr(e, 'status', None),
        )

        return {
            'success': False,
            'error_code': 'brevo_api_error',
            'error': 'Email provider rejected the message.',
        }

    except Exception:
        logger.exception(
            "Brevo email delivery failed template=%s",
            template_name,
        )

        return {
            'success': False,
            'error_code': 'brevo_delivery_error',
            'error': 'Email delivery failed.',
        }


# ============================================
# TELERIVET - SMS
# ============================================

def normalize_phone_number(raw, default_country_code='509'):
    """
    Mete nimewo a nan fòma entènasyonal.

    Egzanp:
    37123456       -> +50937123456
    50937123456    -> +50937123456
    +50937123456   -> +50937123456
    0050937123456  -> +50937123456

    Retounen None si nimewo a pa valab.
    """
    if not raw:
        return None

    raw = str(raw).strip()
    digits = ''.join(ch for ch in raw if ch.isdigit())

    if not digits:
        return None

    if raw.startswith('+'):
        number = digits
    elif digits.startswith('00'):
        number = digits[2:]
    elif len(digits) == 8:
        number = default_country_code + digits
    else:
        number = digits

    if not (8 <= len(number) <= 15):
        return None

    return '+' + number


def get_sms_number(user, source=None):
    """
    Chèche nimewo SMS la:
    1. user.phone_number
    2. source.telephone

    Retounen nimewo entènasyonal la oswa None.
    """
    for candidate in (
        getattr(user, 'phone_number', None),
        getattr(source, 'telephone', None),
    ):
        number = normalize_phone_number(candidate)

        if number:
            return number

    return None


def send_telerivet_sms(to_number, message_text):
    if not to_number:
        return {
            'success': False,
            'error_code': 'missing_recipient',
            'error': 'Recipient phone number is required.',
        }

    if (
        not settings.TELERIVET_API_KEY
        or not settings.TELERIVET_PROJECT_ID
    ):
        logger.error(
            "Telerivet delivery skipped: required settings "
            "are not configured."
        )

        return {
            'success': False,
            'error_code': 'telerivet_not_configured',
            'error': 'SMS delivery is not configured.',
        }

    if APIClient is None:
        logger.error(
            "Telerivet delivery skipped: SDK is not installed."
        )

        return {
            'success': False,
            'error_code': 'telerivet_sdk_missing',
            'error': 'SMS delivery is unavailable.',
        }

    try:
        client = APIClient(settings.TELERIVET_API_KEY)

        project = client.init_project_by_id(
            settings.TELERIVET_PROJECT_ID
        )

        to_number = normalize_phone_number(to_number)

        if not to_number:
            return {
                'success': False,
                'error_code': 'invalid_phone_number',
                'error': 'Invalid phone number.',
            }

        result = project.send_message(
            to_number=to_number,
            content=message_text,
        )

        message_id = getattr(result, 'id', None)

        logger.info(
            "Telerivet SMS submitted message_id=%s",
            message_id,
        )

        return {
            'success': True,
            'message_id': message_id,
            'response': result,
        }

    except Exception:
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
    return user.get_full_name() or user.first_name or user.email


# ============================================
# 1. NOTIFIKASYON POU ENSKRIPSYON
# ============================================

def send_enrollment_confirmation_email(
    user,
    enrollment,
    course_details=None,
):
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
        'course_id': enrollment.cours.pk,
        'instructor': (
            enrollment.cours.instructor.get_full_name()
            if hasattr(enrollment.cours, 'instructor')
            and enrollment.cours.instructor
            else 'Notre équipe'
        ),
        'start_date': (
            enrollment.cours.start_date.strftime('%d/%m/%Y')
            if hasattr(enrollment.cours, 'start_date')
            and enrollment.cours.start_date
            else 'Immédiat'
        ),
        'enrollment_date': enrollment.date_demande.strftime(
            '%d/%m/%Y à %H:%M'
        ),
        'status': enrollment.get_statut_display(),
        'payment_method': enrollment.get_methode_paiement_display(),
        'is_paid': (
            enrollment.methode_paiement not in ['manual', 'subscription']
            and enrollment.methode_paiement != ''
        ),
    }

    if enrollment.methode_paiement == 'subscription':
        template_name = 'enrollment_subscription.html'

    elif enrollment.m
