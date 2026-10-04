from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class UpdateActivityMiddleware(MiddlewareMixin):
    """Met ajou aktivite itilizatè a (maksimòm yon fwa chak 10 minit)."""

    def process_request(self, request):
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and hasattr(user, "last_activity"):
            delta = timezone.now() - user.last_activity
            if delta.total_seconds() > 600:
                user.last_activity = timezone.now()
                user.save(update_fields=["last_activity"])