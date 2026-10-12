from decimal import Decimal

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from enrollments.models import Enrollment


@receiver(pre_save, sender=Enrollment, dispatch_uid="referrals.capture_enrollment_state")
def capture_enrollment_state(sender, instance, **kwargs):
    instance._referral_previous_status = None
    if instance.pk:
        instance._referral_previous_status = (
            sender.objects.filter(pk=instance.pk)
            .values_list("statut", flat=True)
            .first()
        )


@receiver(post_save, sender=Enrollment, dispatch_uid="referrals.reward_paid_enrollment")
def reward_paid_enrollment(sender, instance, created, **kwargs):
    previous = getattr(instance, "_referral_previous_status", None)
    if (
        instance.statut != "active"
        or previous == instance.statut
        or not instance.cours.est_payant
        or instance.methode_paiement not in ("moncash", "natcash")
    ):
        return

    from .services import calculate_discount, is_system_active, on_course_purchase

    if not is_system_active("referral_system"):
        return

    discount = calculate_discount(instance.utilisateur, instance.cours.prix)
    amount_paid = (
        instance.cours.prix * (Decimal("100") - discount) / Decimal("100")
    ).quantize(Decimal("0.01"))
    on_course_purchase(
        user=instance.utilisateur,
        course=instance.cours,
        amount_paid=amount_paid,
        reference_id=instance.pk,
    )
