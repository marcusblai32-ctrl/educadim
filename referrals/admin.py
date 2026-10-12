from django.contrib import admin

from .models import (
    PointTransaction,
    Rating,
    RatingPrompt,
    Referral,
    ReferralCode,
    ReferralConfig,
    ReferralReward,
    RewardTier,
    StaffMember,
    SystemFlag,
    UserPoints,
    WithdrawalRequest,
)


@admin.register(SystemFlag)
class SystemFlagAdmin(admin.ModelAdmin):
    list_display = ("key", "is_active", "updated_at")
    list_editable = ("is_active",)
    readonly_fields = ("updated_at",)


@admin.register(ReferralConfig)
class ReferralConfigAdmin(admin.ModelAdmin):
    list_display = ("reward_mode", "points_first_purchase", "cash_percentage_first", "updated_at")

    def has_add_permission(self, request):
        return not ReferralConfig.objects.exists()


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referred", "status", "signed_up_at", "first_purchase_at")
    list_filter = ("status",)
    search_fields = ("referrer__email", "referred__email", "code_used")
    readonly_fields = ("signed_up_at", "first_purchase_at")


@admin.register(ReferralReward)
class ReferralRewardAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referral", "trigger", "points_awarded", "cash_awarded", "awarded_at")
    list_filter = ("trigger",)
    readonly_fields = ("awarded_at",)


@admin.register(UserPoints)
class UserPointsAdmin(admin.ModelAdmin):
    list_display = ("user", "balance", "total_earned", "total_withdrawn", "cash_balance")
    search_fields = ("user__email", "user__first_name", "user__last_name")


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "cash_amount", "type", "source", "created_at")
    list_filter = ("type", "source")
    search_fields = ("user__email", "description")
    readonly_fields = ("created_at",)


@admin.register(RewardTier)
class RewardTierAdmin(admin.ModelAdmin):
    list_display = ("min_points", "max_points", "money_value", "is_active")
    list_editable = ("is_active",)


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "points_amount", "cash_amount", "method", "status", "created_at")
    list_filter = ("status", "method")
    search_fields = ("user__email", "destination")
    readonly_fields = ("created_at", "processed_at", "processed_by")


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "stars", "is_approved", "created_at")
    list_filter = ("is_approved", "stars")
    search_fields = ("user__email", "comment", "course__titre")
    list_editable = ("is_approved",)
    readonly_fields = ("created_at",)


@admin.register(RatingPrompt)
class RatingPromptAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "shown", "created_at")
    list_filter = ("shown",)
    readonly_fields = ("created_at",)


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "display_order", "is_active")
    list_editable = ("display_order", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("name", "bio")
