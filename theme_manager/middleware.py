import logging

from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin

from .services import get_active_theme

logger = logging.getLogger(__name__)

# Chemen ki dwe rete aksesib menm an maintenance
# (/theme/ = CSS ak imaj tèm lan, san sa paj maintenance a pa gen style)
EXEMPT_PREFIXES = ("/dp/", "/static/", "/media/", "/theme/", "/health/", "/i18n/", "/robots.txt")


class MaintenanceMiddleware(MiddlewareMixin):
    """Mode maintenance: staff pase, rès moun jwenn paj 503 (pa 200, pou SEO ak health checks)."""

    def process_request(self, request):
        try:
            if request.path.startswith(EXEMPT_PREFIXES):
                return None

            user = getattr(request, "user", None)
            if user is not None and user.is_authenticated and user.is_staff:
                return None

            theme = get_active_theme(request)
            if not theme or not theme.maintenance_mode:
                return None

            response = render(request, "maintenance.html", {"message": theme.maintenance_message, "theme": theme}, status=503)
            response["Retry-After"] = "3600"
            response["Cache-Control"] = "no-store"
            return response
        except Exception:
            logger.exception("Unhandled exception in MaintenanceMiddleware")
            return None
