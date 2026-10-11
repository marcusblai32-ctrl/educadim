from django.db.models.signals import post_save
from django.dispatch import receiver

from progress.models import ProgresCours

from .models import Certificate


@receiver(
    post_save,
    sender=ProgresCours,
    dispatch_uid="certificates.create_request_when_course_completed",
)
def create_certificate_request(sender, instance, **kwargs):
    if instance.pourcentage < 100:
        return

    Certificate.objects.get_or_create(
        student=instance.utilisateur,
        course=instance.cours,
        defaults={
            "student_name": (
                instance.utilisateur.get_full_name()
                or instance.utilisateur.email
            ),
            "completed_at": instance.date_modification,
        },
    )
