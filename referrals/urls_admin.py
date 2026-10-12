from django.urls import path

from . import views


urlpatterns = [
    path("admin/flags/", views.system_toggle, name="admin_flags"),
    path("admin/config/", views.referral_config, name="admin_config"),
    path("admin/tiers/", views.reward_tiers, name="admin_tiers"),
    path("admin/tiers/<int:pk>/", views.reward_tier_edit, name="admin_tier_edit"),
    path("admin/tiers/<int:pk>/delete/", views.reward_tier_delete, name="admin_tier_delete"),
    path("admin/withdrawals/", views.withdrawal_list, name="admin_withdrawals"),
    path(
        "admin/withdrawals/<int:pk>/<str:action>/",
        views.withdrawal_process,
        name="admin_withdrawal_process",
    ),
    path("admin/transactions/", views.all_transactions, name="admin_transactions"),
    path("admin/referrals/", views.all_referrals, name="admin_referrals"),
    path(
        "admin/ratings/<int:pk>/approve/",
        views.approve_rating,
        name="admin_approve_rating",
    ),
    path("admin/staff/", views.staff_members, name="admin_staff"),
]
