from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import CustomUser
from utils.notifications import notify_safely, send_notification


class Command(BaseCommand):
    help = "Voye yon avètisman bay itilizatè inaktif (email + SMS si nimewo a la)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, help="Jou inaktivite (default 90)")
        parser.add_argument("--delete-after", type=int, default=120, help="Jou avan efasman (default 120)")
        parser.add_argument("--dry-run", action="store_true", help="Montre sa ki t ap voye san voye l")

    def send_notification(self, user, days_inactive, delete_after_days):
        """Voye avètisman an. Itilize pa admin action nan accounts/admin.py."""
        message = (
            f"votre compte est inactif depuis plus de {days_inactive} jours. "
            f"Connectez-vous pour le conserver, sinon il pourra être supprimé après {delete_after_days} jours."
        )
        return notify_safely(
            send_notification,
            user=user,
            subject="Votre compte EducaDim est inactif",
            message=message,
            send_email=bool(user.email),
            send_sms=bool(user.phone_number),
        )

    def handle(self, *args, **options):
        days = options["days"]
        delete_after = options["delete_after"]
        sent = 0
        users = CustomUser.objects.filter(is_active=True, notification_sent=False, is_staff=False)
        for user in users:
            if not user.is_inactive(days):
                continue
            if options["dry_run"]:
                self.stdout.write(f"[dry-run] {user.user_id} {user.email}")
                continue
            self.send_notification(user, days, delete_after)
            user.notification_sent = True
            user.notification_date = timezone.now()
            user.save(update_fields=["notification_sent", "notification_date"])
            sent += 1
        self.stdout.write(self.style.SUCCESS(f"{sent} notification(s) envoyée(s)."))