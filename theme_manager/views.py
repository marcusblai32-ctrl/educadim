import logging

from django.http import Http404, HttpResponse, HttpResponseNotModified
from django.shortcuts import render

from .services import build_css, css_version, get_active_theme

logger = logging.getLogger(__name__)


def dynamic_css(request):
    """
    CSS dinamik tèm aktif la.
    Lyen an gen ?v=<hash>: lè tèm lan chanje, hash la chanje, kidonk navigatè a
    pa janm gen vye CSS (cache long) men li pa rechaje CSS la chak paj.
    """
    theme = get_active_theme(request)
    css = build_css(theme)
    version = css_version(theme)
    etag = f'"{version}"'

    if request.META.get("HTTP_IF_NONE_MATCH") == etag:
        return HttpResponseNotModified()

    response = HttpResponse(css, content_type="text/css; charset=utf-8")
    response["ETag"] = etag
    if request.GET.get("v") == version:
        response["Cache-Control"] = "public, max-age=31536000, immutable"
    else:
        response["Cache-Control"] = "public, max-age=300"
    return response


def theme_preview(request):
    """Preview tema aktif la"""
    return render(request, "theme_manager/theme_preview.html", {"theme": get_active_theme(request)})


# ============================================
# IMAJ VIEWS
# ============================================
ALLOWED_IMAGE_FIELDS = {
    "logo", "favicon", "hero_image", "about_image", "evenement_banner", "evenement_logo",
}
CONTENT_TYPES = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
    "webp": "image/webp", "ico": "image/x-icon", "svg": "image/svg+xml",
}


def serve_theme_image(request, field_name):
    """Sèvi imaj tèm yo (sèlman chan imaj ki otorize yo)."""
    if field_name not in ALLOWED_IMAGE_FIELDS:
        raise Http404("Image not found")
    theme = get_active_theme(request)
    image_field = getattr(theme, field_name, None) if theme else None
    if image_field and image_field.name:
        try:
            ext = image_field.name.rsplit(".", 1)[-1].lower()
            response = HttpResponse(
                image_field.read(), content_type=CONTENT_TYPES.get(ext, "application/octet-stream")
            )
            response["Cache-Control"] = "public, max-age=86400"
            response["X-Content-Type-Options"] = "nosniff"
            if ext == "svg":
                response["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'"
            return response
        except Exception:
            logger.exception("Error serving theme image %s", field_name)
    raise Http404("Image not found")


def theme_logo(request):
    return serve_theme_image(request, "logo")


def theme_favicon(request):
    return serve_theme_image(request, "favicon")


def theme_hero_image(request):
    return serve_theme_image(request, "hero_image")


def theme_about_image(request):
    return serve_theme_image(request, "about_image")


def theme_evenement_banner(request):
    return serve_theme_image(request, "evenement_banner")


def theme_evenement_logo(request):
    return serve_theme_image(request, "evenement_logo")
