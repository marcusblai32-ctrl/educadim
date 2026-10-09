import logging

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Telerivet se opsyonèl. Si li pa enstale, imel yo ka toujou fonksyone.
try:
    from telerivet import API as APIClient
except ImportError:
    APIClient = None


def send_brevo_email(
    subject,
    to_email,
    template_name=None,
    context=None,
    plain_message=None,
):
    """
    Voye yon imel atravè Brevo.

    Ou ka itilize yon template HTML oswa yon mesaj tèks senp.
    """
    if not to_email:
        logger.warning("Imel la pa voye: adrès moun k ap resevwa a manke.")
        return False

    api_key = getattr(settings, "BREVO_API_KEY", None)

    if not api_key:
        logger.error("BREVO_API_KEY pa defini nan settings yo.")
        return False

    context = context or {}

    try:
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key["api-key"] = api_key

        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        sender_email = getattr(
            settings,
            "DEFAULT_FROM_EMAIL",
            None,
        )

        sender_name = getattr(
            settings,
            "SITE_NAME",
            "EducaDim",
        )

        if not sender_email:
            logger.error("DEFAULT_FROM_EMAIL pa defini.")
            return False

        if template_name:
            html_content = render_to_string(
                f"emails/{template_name}",
                context,
            )
            text_content = strip_tags(html_content)
        else:
            text_content = plain_message or ""
            html_content = None

        email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": to_email}],
            sender={
                "email": sender_email,
                "name": sender_name,
            },
            subject=subject,
            text_content=text_content,
            html_content=html_content,
        )

        api_instance.send_transac_email(email)

        logger.info("Imel voye avèk siksè bay %s", to_email)
        return True

    except ApiException as exc:
        logger.exception("Erè Brevo pandan voye imel la: %s", exc)
        return False

    except Exception as exc:
        logger.exception("Erè pandan voye imel la: %s", exc)
        return False


def normalize_phone_number(phone_number):
    """
    Netwaye nimewo telefòn nan san nou pa devine kòd peyi a.
    """
    if not phone_number:
        return None

    phone_number = str(phone_number).strip()

    # Konsève siy + la si li prezan, epi retire lòt karaktè
    # ki pa chif.
    has_plus = phone_number.startswith("+")
    digits = "".join(
        character
        for character in phone_number
        if character.isdigit()
    )

    if not digits:
        return None

    if has_plus:
        return f"+{digits}"

    return digits


def get_sms_number():
    """
    Retounen nimewo Telerivet ki defini nan Django settings yo.
    """
    return (
        getattr(settings, "TELERIVET_PHONE_ID", None)
        or getattr(settings, "TELERIVET_NUMBER_ID", None)
    )


def send_telerivet_sms(phone_number, message):
    """
    Voye yon SMS atravè Telerivet.

    Asire w Telerivet enstale epi varyab anviwònman yo defini.
    """
    if not APIClient:
        logger.warning(
            "Telerivet pa disponib. Verifye depandans telerivet la."
        )
        return False

    api_key = getattr(settings, "TELERIVET_API_KEY", None)
    project_id = getattr(settings, "TELERIVET_PROJECT_ID", None)

    normalized_number = normalize_phone_number(phone_number)

    if not api_key or not project_id:
        logger.error(
            "TELERIVET_API_KEY oswa TELERIVET_PROJECT_ID manke."
        )
        return False

    if not normalized_number:
        logger.warning("SMS la pa voye: nimewo telefòn nan pa valab.")
        return False

    if not message:
        logger.warning("SMS la pa voye: mesaj la vid.")
        return False

    try:
        client = APIClient(api_key)
        project = client.initProjectById(project_id)

        project.sendMessage(
            to_number=normalized_number,
            content=message,
        )

        logger.info("SMS voye avèk siksè bay %s", normalized_number)
        return True

    except Exception as exc:
        logger.exception("Erè Telerivet pandan voye SMS la: %s", exc)
        return False


def get_user_full_name(user):
    """
    Retounen non konplè itilizatè a.
    """
    if not user:
        return ""

    full_name = ""

    if hasattr(user, "get_full_name"):
        full_name = user.get_full_name()

    if full_name:
        return full_name.strip()

    return (
        getattr(user, "first_name", "")
        or getattr(user, "username", "")
        or getattr(user, "email", "")
        or ""
    )


def get_user_email(user):
    """
    Retounen adrès imel itilizatè a.
    """
    if not user:
        return None

    return getattr(user, "email", None)


def get_user_phone(user):
    """
    Chèche nimewo telefòn itilizatè a sou kèk non chan komen.
    """
    if not user:
        return None

    possible_fields = (
        "phone_number",
        "telephone",
        "phone",
        "numero_telephone",
    )

    for field_name in possible_fields:
        value = getattr(user, field_name, None)

        if value:
            return normalize_phone_number(value)

    return None


def send_user_notification(
    user,
    subject,
    message,
    template_name=None,
    context=None,
    send_email=True,
    send_sms=False,
):
    """
    Voye notifikasyon bay yon itilizatè pa imel, SMS, oswa toude.

    Fonksyon an retounen True si omwen youn nan metòd yo reyisi.
    """
    if not user:
        logger.warning("Notifikasyon an pa voye: itilizatè a manke.")
        return False

    context = context or {}
    context.setdefault("user", user)
    context.setdefault("user_name", get_user_full_name(user))
    context.setdefault("subject", subject)
    context.setdefault("message", message)

    success = False

    if send_email:
        email_address = get_user_email(user)

        if email_address:
            email_success = send_brevo_email(
                subject=subject,
                to_email=email_address,
                template_name=template_name,
                context=context,
                plain_message=message,
            )

            success = success or email_success

    if send_sms:
        phone_number = get_user_phone(user)

        if phone_number:
            sms_success = send_telerivet_sms(
                phone_number=phone_number,
                message=message,
            )

            success = success or sms_success

    return success


# ---------------------------------------------------------
# ENROLLMENT: ENSKRIPSYON NAN YON KOU
# ---------------------------------------------------------

def send_enrollment_confirmation_email(user, course):
    """
    Konfime resepsyon demann enskripsyon yon elèv.
    """
    user_name = get_user_full_name(user)
    course_title = getattr(course, "titre_ht", None) or str(course)

    context = {
        "user": user,
        "user_name": user_name,
        "course": course,
        "course_title": course_title,
    }

    return send_user_notification(
        user=user,
        subject="Konfimasyon enskripsyon — EducaDim",
        message=(
            f"Bonjou {user_name}, nou resevwa demann enskripsyon ou "
            f"pou kou {course_title}. N ap enfòme w sou pwochen etap yo."
        ),
        template_name="enrollment_confirmation.html",
        context=context,
        send_email=True,
        send_sms=False,
    )


def send_enrollment_approved_email(user, course):
    """
    Enfòme elèv la yo apwouve enskripsyon li.
    """
    user_name = get_user_full_name(user)
    course_title = getattr(course, "titre_ht", None) or str(course)

    context = {
        "user": user,
        "user_name": user_name,
        "course": course,
        "course_title": course_title,
    }

    return send_user_notification(
        user=user,
        subject="Enskripsyon ou apwouve — EducaDim",
        message=(
            f"Bonjou {user_name}, enskripsyon ou nan kou "
            f"{course_title} apwouve. Ou kapab konekte sou EducaDim "
            "pou jwenn aksè ak kou a."
        ),
        template_name="enrollment_approved.html",
        context=context,
        send_email=True,
        send_sms=False,
    )


def send_enrollment_rejected_email(user, course, reason=None):
    """
    Enfòme elèv la yo pa apwouve enskripsyon li.
    """
    user_name = get_user_full_name(user)
    course_title = getattr(course, "titre_ht", None) or str(course)

    context = {
        "user": user,
        "user_name": user_name,
        "course": course,
        "course_title": course_title,
        "reason": reason or "",
    }

    message = (
        f"Bonjou {user_name}, demann enskripsyon ou pou kou "
        f"{course_title} pa apwouve pou kounye a."
    )

    if reason:
        message += f" Rezon: {reason}"

    return send_user_notification(
        user=user,
        subject="Enskripsyon — EducaDim",
        message=message,
        template_name="enrollment_rejected.html",
        context=context,
        send_email=True,
        send_sms=False,
    )


# ---------------------------------------------------------
# SUBSCRIPTION: ABÒNMAN
# ---------------------------------------------------------

def send_subscription_confirmation_email(user, subscription=None):
    """
    Konfime resepsyon yon demann abònman.
    """
    user_name = get_user_full_name(user)

    context = {
        "user": user,
        "user_name": user_name,
        "subscription": subscription,
    }

    return send_user_notification(
        user=user,
        subject="Konfimasyon demann abònman — EducaDim",
        message=(
            f"Bonjou {user_name}, nou resevwa demann abònman ou "
            "an. N ap enfòme w lè gen yon mizajou."
        ),
        template_name="subscription_confirmation.html",
        context=context,
        send_email=True,
        send_sms=False,
    )


def send_subscription_approved_email(user, subscription=None):
    """
    Enfòme itilizatè a abònman li apwouve.
    """
    user_name = get_user_full_name(user)

    context = {
        "user": user,
        "user_name": user_name,
        "subscription": subscription,
    }

    return send_user_notification(
        user=user,
        subject="Abònman ou apwouve — EducaDim",
        message=(
            f"Bonjou {user_name}, abònman ou apwouve. "
            "Ou kapab konekte sou EducaDim pou jwenn aksè "
            "ak sèvis ki disponib pou kont ou."
        ),
        template_name="subscription_approved.html",
        context=context,
        send_email=True,
        send_sms=False,
    )


# ---------------------------------------------------------
# PASSWORD RESET: REYINITIALIZASYON MODPAS
# ---------------------------------------------------------

def send_password_reset_email(user, reset_link):
    """
    Voye imel ki gen lyen pou reyinisyalize modpas la.

    Template a dwe egziste nan:
    templates/emails/password_reset_email.html
    """
    user_name = get_user_full_name(user)

    context = {
        "user": user,
        "user_name": user_name,
        "reset_link": reset_link,
    }

    return send_user_notification(
        user=user,
        subject="Reyinisyalize modpas ou — EducaDim",
        message=(
            f"Bonjou {user_name}, sèvi ak lyen sa a pou "
            f"reyinisyalize modpas ou: {reset_link}"
        ),
        template_name="password_reset_email.html",
        context=context,
        send_email=True,
        send_sms=False,
    )


def send_password_reset_sms(user, reset_link):
    """
    Voye yon SMS ki bay lyen reyinisyalizasyon an.
    """
    user_name = get_user_full_name(user)
    phone_number = get_user_phone(user)

    if not phone_number:
        logger.warning(
            "Pa gen nimewo telefòn pou reyinisyalizasyon modpas la."
        )
        return False

    message = (
        f"Bonjou {user_name}, itilize lyen sa a pou "
        f"reyinisyalize modpas EducaDim ou: {reset_link}"
    )

    return send_telerivet_sms(phone_number, message)


# ---------------------------------------------------------
# NOTIFIKASYON JENERIK
# ---------------------------------------------------------

def send_notification_email(
    user,
    subject,
    message,
    template_name=None,
    context=None,
):
    """
    Voye yon notifikasyon imel jeneral.
    """
    return send_user_notification(
        user=user,
        subject=subject,
        message=message,
        template_name=template_name,
        context=context,
        send_email=True,
        send_sms=False,
    )


def send_notification_sms(user, message):
    """
    Voye yon notifikasyon SMS jeneral.
    """
    phone_number = get_user_phone(user)

    if not phone_number:
        logger.warning(
            "Pa gen nimewo telefòn pou notifikasyon SMS la."
        )
        return False

    return send_telerivet_sms(phone_number, message)


def notify_safely(
    user,
    subject,
    message,
    template_name=None,
    context=None,
    send_email=True,
    send_sms=False,
):
    """
    Eseye voye notifikasyon an san yon erè notifikasyon
    pa fè aplikasyon an sispann fonksyone.
    """
    try:
        return send_user_notification(
            user=user,
            subject=subject,
            message=message,
            template_name=template_name,
            context=context,
            send_email=send_email,
            send_sms=send_sms,
        )

    except Exception:
        logger.exception(
            "Erè inatandi pandan voye notifikasyon pou itilizatè a."
        )
        return False
