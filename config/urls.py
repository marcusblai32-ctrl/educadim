from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf.urls.i18n import i18n_patterns
from django.http import JsonResponse, FileResponse, HttpResponse
from django.contrib.sitemaps.views import sitemap
from config.sitemaps import StaticViewSitemap, CourseSitemap
from courses.views import about_page, contact_page, conditions_page, privacy_page, faq_page


admin.site.site_header = "Administration EducDim"
admin.site.site_title = "Administration EducDim"
admin.site.index_title = "Bienvenue dans l'administration EducDim"


sitemaps = {
    "static": StaticViewSitemap,
    "courses": CourseSitemap,
}


def health_check(request):
    return JsonResponse({
        "status": "ok",
        "message": "I am alive!",
    })


def robots_txt(request):
    robots_path = settings.BASE_DIR / "robots.txt"
    return FileResponse(
        open(robots_path, "rb"),
        content_type="text/plain",
    )


def google_verification(request):
    return HttpResponse(
        "google-site-verification: google38eba4ca7aaf104d.html",
        content_type="text/plain",
    )


urlpatterns = [
    path("dp/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("health/", health_check, name="health_check"),

    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),

    path(
        "robots.txt",
        robots_txt,
        name="robots",
    ),

    path(
        "google38eba4ca7aaf104d.html",
        google_verification,
        name="google_verification",
    ),
]


urlpatterns += i18n_patterns(
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("accounts/", include("accounts.urls")),
    path("cours/", include("courses.urls")),
    path("inscriptions/", include("enrollments.urls")),
    path("abonnements/", include("subscriptions.urls")),
    path("progression/", include("progress.urls")),
    path("todo/", include("todo.urls")),
    path("quiz/", include("quiz.urls")),
    path("presence/", include("attendance.urls")),
    path("badges/", include("badges.urls")),
    path("classement/", include("ranking.urls")),
    path("chat/", include("chat.urls")),
    path("notifications/", include("notifications.urls")),
    path("theme/", include("theme_manager.urls")),
    path("ads/", include("ads.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("a-propos/", about_page, name="about"),
    path("contact/", contact_page, name="contact"),
    path("conditions/", conditions_page, name="conditions"),
    path("confidentialite/", privacy_page, name="privacy"),
    path("faq/", faq_page, name="faq"),
    prefix_default_language=True,
)


if settings.DEBUG:
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )