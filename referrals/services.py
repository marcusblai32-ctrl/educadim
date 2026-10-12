import secrets
import string
from decimal import Decimal, ROUND_HALF_UP

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import (
    PointTransaction,
    Referral,
    ReferralCode,
    ReferralConfig,
    ReferralReward,
    RewardTier,
    SystemFlag,
    UserPoints,
    WithdrawalRequest,
)


SYSTEM_KEYS = (
    "referral_system",
    "points_system",
    "discount_system",
    "rating_system",
    "staff_carousel",
    "withdrawal_system",
)


def is_system_active(key):
    if key not in SYSTEM_KEYS:
        return False
    try:
        return SystemFlag.objects.filter(key=key).values_list(
            "is_active", flat=True
        ).first() is not False
    except Exception:
        # The app can be imported before its first migration is applied.
        return True


def get_or_create_referral_code(user):
    existing = ReferralCode.objects.filter(user=user).first()
    if existing:
        return existing

    prefix = "".join(
        char for char in f"{user.last_name}{user.first_name}".upper()
        if char in string.ascii_uppercase
    )[:8] or "INVITE"
    for _ in range(8):
        try:
            return ReferralCode.objects.create(
                user=user,
                code=f"{prefix}{secrets.token_hex(3).upper()}",
            )
        except IntegrityError:
            existing = ReferralCode.objects.filter(user=user).first()
            if existing:
                return existing
    raise IntegrityError("Pa kapab kreye yon kòd referans inik.")


def track_click(code):
    if not is_system_active("referral_system"):
        return None
    try:
        ReferralCode.objects.filter(code=code).update(clicks=F("clicks") + 1)
        return ReferralCode.objects.select_related("user").filter(code=code).first()
    except Exception:
        return None


def _award_reward(referral, trigger, points=0, cash=Decimal("0.00"),
                  source=PointTransaction.Source.REFERRAL_PURCHASE,
                  reference_id=None, description=""):
    """Persist an award and apply each enabled balance component once."""
    if not is_system_active("referral_system"):
        return None

    config = ReferralConfig.load()
    reward_mode = config.reward_mode
    points_enabled = (
        reward_mode in (ReferralConfig.RewardMode.POINTS, ReferralConfig.RewardMode.BOTH)
        and points > 0
        and is_system_active("points_system")
    )
    cash_enabled = (
        reward_mode in (ReferralConfig.RewardMode.CASH, ReferralConfig.RewardMode.BOTH)
        and cash > 0
    )
    effective_points = int(points) if points_enabled else 0
    effective_cash = cash.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if cash_enabled else Decimal("0.00")

    with transaction.atomic():
        try:
            with transaction.atomic():
                reward = ReferralReward.objects.create(
                    referral=referral,
                    referrer=referral.referrer,
                    trigger=trigger,
                    points_awarded=effective_points,
                    cash_awarded=effective_cash,
                    reference_id=reference_id,
                )
        except IntegrityError:
            return None

        if effective_points:
            balance, _ = UserPoints.objects.get_or_create(user=referral.referrer)
            UserPoints.objects.filter(pk=balance.pk).update(
                balance=F("balance") + effective_points,
                total_earned=F("total_earned") + effective_points,
            )
            PointTransaction.objects.create(
                user=referral.referrer,
                amount=effective_points,
                cash_amount=effective_cash,
                type=PointTransaction.Direction.CREDIT,
                source=source,
                reference_id=reference_id or reward.pk,
                description=description,
            )
        if effective_cash:
            balance, _ = UserPoints.objects.get_or_create(user=referral.referrer)
            UserPoints.objects.filter(pk=balance.pk).update(
                cash_balance=F("cash_balance") + effective_cash
            )
            if not effective_points:
                PointTransaction.objects.create(
                    user=referral.referrer,
                    amount=0,
                    cash_amount=effective_cash,
                    type=PointTransaction.Direction.CREDIT,
                    source=source,
                    reference_id=reference_id or reward.pk,
                    description=description,
                )
        return reward


def register_with_referral(new_user, code):
    if not code or not is_system_active("referral_system"):
        return None
    referral_code = ReferralCode.objects.select_related("user").filter(code=code).first()
    if not referral_code or referral_code.user_id == new_user.pk:
        return None
    referral, created = Referral.objects.get_or_create(
        referred=new_user,
        defaults={
            "referrer": referral_code.user,
            "code_used": referral_code.code,
            "status": Referral.Status.SIGNED_UP,
        },
    )
    if not created:
        return referral

    config = ReferralConfig.load()
    _award_reward(
        referral,
        ReferralReward.Trigger.SIGNUP,
        points=config.points_signup,
        source=PointTransaction.Source.REFERRAL_SIGNUP,
        description=f"Rekonpans pou enskripsyon {new_user.get_full_name()}",
    )
    return referral


def on_course_purchase(user, course, amount_paid, reference_id=None):
    """Reward a referred learner after a verified paid enrollment."""
    if not is_system_active("referral_system"):
        return None
    referral = Referral.objects.select_related("referrer").filter(referred=user).first()
    if not referral:
        return None

    with transaction.atomic():
        referral = Referral.objects.select_for_update().get(pk=referral.pk)
        previous_purchases = referral.rewards.filter(
            trigger__in=(
                ReferralReward.Trigger.FIRST_PURCHASE,
                ReferralReward.Trigger.REPEAT_PURCHASE,
            )
        ).count()
        trigger = (
            ReferralReward.Trigger.FIRST_PURCHASE
            if previous_purchases == 0
            else ReferralReward.Trigger.REPEAT_PURCHASE
        )
        config = ReferralConfig.load()
        points = (
            config.points_first_purchase
            if trigger == ReferralReward.Trigger.FIRST_PURCHASE
            else config.points_repeat_purchase
        )
        percentage = (
            config.cash_percentage_first
            if trigger == ReferralReward.Trigger.FIRST_PURCHASE
            else config.cash_percentage_repeat
        )
        cash = (Decimal(str(amount_paid)) * percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        reward = _award_reward(
            referral,
            trigger,
            points=points,
            cash=cash,
            reference_id=reference_id,
            description=f"Rekonpans pou acha kou: {course}",
        )
        if reward and trigger == ReferralReward.Trigger.FIRST_PURCHASE:
            referral.status = Referral.Status.PURCHASED
            referral.first_purchase_at = timezone.now()
            referral.save(update_fields=("status", "first_purchase_at"))
        return reward


def add_points(user, amount, source, ref_id=None, description=""):
    if amount <= 0 or not is_system_active("points_system"):
        return None
    with transaction.atomic():
        balance, _ = UserPoints.objects.get_or_create(user=user)
        UserPoints.objects.filter(pk=balance.pk).update(
            balance=F("balance") + amount,
            total_earned=F("total_earned") + amount,
        )
        return PointTransaction.objects.create(
            user=user,
            amount=amount,
            type=PointTransaction.Direction.CREDIT,
            source=source,
            reference_id=ref_id,
            description=description,
        )


def deduct_points(user, amount, source, ref_id=None, description=""):
    if amount <= 0 or not is_system_active("points_system"):
        return None
    with transaction.atomic():
        balance = UserPoints.objects.select_for_update().filter(user=user).first()
        if not balance or balance.balance < amount:
            return None
        UserPoints.objects.filter(pk=balance.pk).update(balance=F("balance") - amount)
        return PointTransaction.objects.create(
            user=user,
            amount=-amount,
            type=PointTransaction.Direction.DEBIT,
            source=source,
            reference_id=ref_id,
            description=description,
        )


def add_cash(user, amount, source, ref_id=None, description=""):
    amount = Decimal(str(amount))
    if amount <= 0 or not is_system_active("referral_system"):
        return None
    with transaction.atomic():
        balance, _ = UserPoints.objects.get_or_create(user=user)
        UserPoints.objects.filter(pk=balance.pk).update(
            cash_balance=F("cash_balance") + amount
        )
        return PointTransaction.objects.create(
            user=user,
            amount=0,
            cash_amount=amount,
            type=PointTransaction.Direction.CREDIT,
            source=source,
            reference_id=ref_id,
            description=description,
        )


def request_withdrawal(user, points, method, destination):
    if (
        not is_system_active("withdrawal_system")
        or not is_system_active("points_system")
    ):
        return None
    try:
        points = int(points)
    except (TypeError, ValueError):
        return None
    config = ReferralConfig.load()
    if points < config.minimum_withdrawal_points:
        return None
    tier = RewardTier.objects.filter(
        is_active=True, min_points__lte=points, max_points__gte=points
    ).order_by("min_points").first()
    if not tier:
        return None
    with transaction.atomic():
        balance = UserPoints.objects.select_for_update().filter(user=user).first()
        if not balance or balance.balance < points:
            return None
        UserPoints.objects.filter(pk=balance.pk).update(
            balance=F("balance") - points,
        )
        request = WithdrawalRequest.objects.create(
            user=user,
            points_amount=points,
            cash_amount=tier.money_value,
            method=method,
            destination=destination,
        )
        PointTransaction.objects.create(
            user=user,
            amount=-points,
            cash_amount=tier.money_value,
            type=PointTransaction.Direction.DEBIT,
            source=PointTransaction.Source.WITHDRAWAL,
            reference_id=request.pk,
            description=f"Demand retrè {request.pk}",
        )
        return request


def request_cash_withdrawal(user, amount, method, destination):
    if not is_system_active("withdrawal_system") or not is_system_active("referral_system"):
        return None
    amount = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        return None
    with transaction.atomic():
        balance = UserPoints.objects.select_for_update().filter(user=user).first()
        if not balance or balance.cash_balance < amount:
            return None
        UserPoints.objects.filter(pk=balance.pk).update(
            cash_balance=F("cash_balance") - amount
        )
        request = WithdrawalRequest.objects.create(
            user=user,
            points_amount=0,
            cash_amount=amount,
            method=method,
            destination=destination,
        )
        PointTransaction.objects.create(
            user=user,
            amount=0,
            cash_amount=-amount,
            type=PointTransaction.Direction.DEBIT,
            source=PointTransaction.Source.WITHDRAWAL,
            reference_id=request.pk,
            description=f"Demann retrè lajan {request.pk}",
        )
        return request


def process_withdrawal(request_id, status, processed_by):
    if not is_system_active("withdrawal_system"):
        return None
    if status not in (WithdrawalRequest.Status.APPROVED, WithdrawalRequest.Status.REJECTED):
        return None
    with transaction.atomic():
        request = WithdrawalRequest.objects.select_for_update().get(pk=request_id)
        if (
            (request.points_amount and not is_system_active("points_system"))
            or (not request.points_amount and not is_system_active("referral_system"))
        ):
            return None
        if request.status != WithdrawalRequest.Status.PENDING:
            return request
        request.status = status
        request.processed_by = processed_by
        request.processed_at = timezone.now()
        request.save(update_fields=("status", "processed_by", "processed_at"))
        if (
            status == WithdrawalRequest.Status.APPROVED
            and request.points_amount
        ):
            UserPoints.objects.filter(user=request.user).update(
                total_withdrawn=F("total_withdrawn") + request.points_amount
            )
        elif status == WithdrawalRequest.Status.REJECTED:
            balance, _ = UserPoints.objects.get_or_create(user=request.user)
            if request.points_amount:
                UserPoints.objects.filter(pk=balance.pk).update(
                    balance=F("balance") + request.points_amount,
                )
            else:
                UserPoints.objects.filter(pk=balance.pk).update(
                    cash_balance=F("cash_balance") + request.cash_amount
                )
            PointTransaction.objects.create(
                user=request.user,
                amount=request.points_amount,
                cash_amount=request.cash_amount,
                type=PointTransaction.Direction.CREDIT,
                source=PointTransaction.Source.WITHDRAWAL,
                reference_id=request.pk,
                description=f"Retou apre refi demand {request.pk}",
            )
        return request


def calculate_discount(user, price=None):
    if (
        not getattr(user, "is_authenticated", False)
        or not is_system_active("discount_system")
        or not is_system_active("points_system")
    ):
        return Decimal("0.00")
    try:
        balance = user.reward_points.balance
    except UserPoints.DoesNotExist:
        return Decimal("0.00")
    config = ReferralConfig.load()
    if balance < config.discount_points_threshold:
        return Decimal("0.00")
    return config.discount_percentage


def get_referral_stats(user):
    if not is_system_active("referral_system"):
        return {"referral_count": 0, "purchased_count": 0, "points_earned": 0}
    referrals = Referral.objects.filter(referrer=user)
    rewards = ReferralReward.objects.filter(referrer=user)
    return {
        "referral_count": referrals.count(),
        "purchased_count": referrals.filter(status=Referral.Status.PURCHASED).count(),
        "points_earned": sum(rewards.values_list("points_awarded", flat=True)),
    }


def get_all_referrals(filters=None):
    queryset = Referral.objects.select_related("referrer", "referred")
    if filters:
        status = filters.get("status")
        if status in Referral.Status.values:
            queryset = queryset.filter(status=status)
    return queryset
