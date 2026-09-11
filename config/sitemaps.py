from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation
from courses.models import Course

LANGUAGES = ["fr", "ht"]


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    view_names = [
        "home",
        "about",
        "contact",
        "conditions",
        "privacy",
        "faq",
        "courses:course_list",
    ]

    def items(self):
        return [
            (language, view_name)
            for language in LANGUAGES
            for view_name in self.view_names
        ]

    def location(self, item):
        language, view_name = item

        with translation.override(language):
            return reverse(view_name)


class CourseSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        courses = Course.objects.filter(publie=True).order_by("pk")

        return [
            (language, course)
            for language in LANGUAGES
            for course in courses
        ]

    def location(self, item):
        language, course = item

        with translation.override(language):
            return reverse(
                "courses:course_detail",
                kwargs={"pk": course.pk},
            )

    def lastmod(self, item):
        course = item[1]
        return course.updated_at