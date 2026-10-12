from django.urls import path

from . import views
from .urls_admin import urlpatterns as admin_urlpatterns

app_name = "referrals"

urlpatterns = [
    path("r/<str:code>/", views.referral_link, name="track"),
    path("pwen/", views.my_points, name="my_points"),
    path("envitasyon/", views.my_referrals, name="my_referrals"),
    path("retrè/", views.withdrawal_request, name="withdrawal"),
    path("evalye/", views.submit_rating, name="submit_rating"),
    path("evalye/prompt-shown/", views.mark_rating_prompt, name="mark_rating_prompt"),
]

urlpatterns += admin_urlpatterns
