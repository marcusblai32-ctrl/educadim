from django.apps import AppConfig


class ReferralsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "referrals"
    verbose_name = "Parrainage et récompenses"

    def ready(self):
        from . import signals  # noqa: F401
