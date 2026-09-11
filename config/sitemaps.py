from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

from courses.models import Course


SUPPORTED_LANGUAGES = ["fr", "ht"]


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return [
            "home",
            "about",
            "contact",
            "conditions",
            "privacy",
            "faq",
            "courses:course_list",
        ]

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []

        for language in SUPPORTED_LANGUAGES:
            with translation.override(language):
                for item in self.items():
                    urls.append({
                        "item": item,
                        "location": self.location(item),
                        "lastmod": None,
                        "changefreq": self.changefreq,
                        "priority": self.priority,
                    })

        return urls


class CourseSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Course.objects.filter(
            publie=True
        ).order_by("pk")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse(
            "courses:course_detail",
            kwargs={"pk": obj.pk},
        )

    def get_urls(self, page=1, site=None, protocol=None):
        urls = []

        for language in SUPPORTED_LANGUAGES:
            with translation.override(language):
                for obj in self.paginator.page(page).object_list:
                    urls.append({
                        "item": obj,
                        "location": self.location(obj),
                        "lastmod": self.lastmod(obj),
                        "changefreq": self.changefreq,
                        "priority": self.priority,
                    })

        return urls