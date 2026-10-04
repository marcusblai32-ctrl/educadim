from django.utils import timezone

from .models import Subscription, SubscriptionCourseSelection


def active_subscription_for_course(user, course):
    """
    Retounen abònman aktif (ki poko ekspire) ki kouvri kou a, oswa None.
    LI SÈLMAN: pa janm ekri nan baz done a.
    """
    if user is None or not user.is_authenticated:
        return None
    now = timezone.now()

    # 1. Plan san limit (max_courses=0) ki gen kou sa a
    sub = (
        Subscription.objects.filter(
            utilisateur=user,
            statut="active",
            plan__max_courses=0,
            plan__cours=course,
            date_fin__gt=now,
        )
        .select_related("plan")
        .first()
    )
    if sub:
        return sub

    # 2. Plan ak limit kote itilizatè a chwazi kou sa a
    selection = (
        SubscriptionCourseSelection.objects.filter(
            subscription__utilisateur=user,
            subscription__statut="active",
            subscription__date_fin__gt=now,
            course=course,
        )
        .select_related("subscription")
        .first()
    )
    return selection.subscription if selection else None