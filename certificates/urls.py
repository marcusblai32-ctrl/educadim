from django.urls import path

from . import views

app_name = "certificates"

urlpatterns = [
    path("", views.my_certificates, name="mine"),
    path("verifier/<uuid:public_id>/", views.verify_certificate, name="verify"),
    path(
        "<uuid:public_id>/details/",
        views.submit_certificate_details,
        name="submit_details",
    ),
    path("<uuid:public_id>/pdf/", views.download_certificate, name="download"),
    path("staff/", views.review_queue, name="review_queue"),
    path("staff/<uuid:public_id>/", views.review_certificate, name="review"),
]
