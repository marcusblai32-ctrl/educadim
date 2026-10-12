from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class SystemFlag(models.Model):
    key = models.SlugField(max_length=40, unique=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("key",)
        verbose_name = "Activation de fonctionnalité"
        verbose_name_plural = "Activations de fonctionnalités"

    def __str__(self):
        return f"{self.key}: {'active' if self.is_active else 'inactive'}"


class ReferralCode(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_code",
    )
    code = models.CharField(max_length=32, unique=True)
    clicks = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


class Referral(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        SIGNED_UP = "signed_up", "Inscrit"
        PURCHASED = "purchased", "A acheté"
        EXPIRED = "expired", "Expiré"

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referrals_sent",
    )
    referred = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_source",
    )
    code_used = models.CharField(max_length=32)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.SIGNED_UP
    )
    signed_up_at = models.DateTimeField(auto_now_add=True)
    first_purchase_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-signed_up_at",)

    def __str__(self):
        return f"{self.referrer} → {self.referred}"


class ReferralReward(models.Model):
    class Trigger(models.TextChoices):
        SIGNUP = "signup", "Enskripsyon"
        FIRST_PURCHASE = "first_purchase", "Premye acha"
        REPEAT_PURCHASE = "repeat_purchase", "Acha repete"

    referral = models.ForeignKey(
        Referral, on_delete=models.CASCADE, related_name="rewards"
    )
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="referral_rewards",
    )
    trigger = models.CharField(max_length=20, choices=Trigger.choices)
    points_awarded = models.PositiveIntegerField(default=0)
    cash_awarded = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    reference_id = models.PositiveBigIntegerField(null=True, blank=True, unique=True)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-awarded_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("referral", "trigger"),
                condition=models.Q(trigger="signup"),
                name="unique_referral_signup_reward",
            ),
        ]

    def __str__(self):
        return f"{self.trigger}: {self.referrer}"


class ReferralConfig(models.Model):
    class RewardMode(models.TextChoices):
        POINTS = "points", "Pwen sèlman"
        CASH = "cash", "Lajan sèlman"
        BOTH = "both", "Pwen ak lajan"

    points_signup = models.PositiveIntegerField(default=0)
    points_first_purchase = models.PositiveIntegerField(default=50)
    points_repeat_purchase = models.PositiveIntegerField(default=20)
    cash_percentage_first = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    cash_percentage_repeat = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    reward_mode = models.CharField(
        max_length=10, choices=RewardMode.choices, default=RewardMode.POINTS
    )
    discount_points_threshold = models.PositiveIntegerField(default=100)
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00"),
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    minimum_withdrawal_points = models.PositiveIntegerField(default=100)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paramèt rekonpans"
        verbose_name_plural = "Paramèt rekonpans"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class UserPoints(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reward_points",
    )
    balance = models.PositiveIntegerField(default=0)
    total_earned = models.PositiveIntegerField(default=0)
    total_withdrawn = models.PositiveIntegerField(default=0)
    cash_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {self.balance} pwen"


class PointTransaction(models.Model):
    class Direction(models.TextChoices):
        CREDIT = "credit", "Kredi"
        DEBIT = "debit", "Debi"

    class Source(models.TextChoices):
        REFERRAL_SIGNUP = "referral_signup", "Enskripsyon referans"
        REFERRAL_PURCHASE = "referral_purchase", "Acha referans"
        CERTIFICATE = "certificate", "Sètifika"
        GRADE = "grade", "Nòt"
        WITHDRAWAL = "withdrawal", "Retrè"
        DISCOUNT = "discount", "Rabè"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="point_transactions",
    )
    amount = models.IntegerField()
    cash_amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    type = models.CharField(max_length=8, choices=Direction.choices)
    source = models.CharField(max_length=24, choices=Source.choices)
    reference_id = models.PositiveBigIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("user", "created_at"))]


class RewardTier(models.Model):
    min_points = models.PositiveIntegerField()
    max_points = models.PositiveIntegerField()
    money_value = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ("min_points",)
        constraints = [
            models.CheckConstraint(
                condition=models.Q(max_points__gte=models.F("min_points")),
                name="reward_tier_max_gte_min",
            ),
        ]

    def __str__(self):
        return f"{self.min_points}–{self.max_points} pwen"


class WithdrawalRequest(models.Model):
    class Method(models.TextChoices):
        MONCASH = "moncash", "MonCash"
        NATCASH = "natcash", "NatCash"
        BANK = "bank", "Transfè labank"

    class Status(models.TextChoices):
        PENDING = "pending", "An atant"
        APPROVED = "approved", "Apwouve"
        REJECTED = "rejected", "Refize"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="withdrawal_requests",
    )
    points_amount = models.PositiveIntegerField()
    cash_amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=12, choices=Method.choices)
    destination = models.CharField(max_length=160)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_withdrawals",
    )

    class Meta:
        ordering = ("-created_at",)


class Rating(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ratings"
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ratings",
    )
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("is_approved", "created_at"))]

    def __str__(self):
        return f"{self.stars}/5 — {self.user}"


class RatingPrompt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="rating_prompts",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="rating_prompts",
    )
    shown = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "course"),
                condition=models.Q(course__isnull=False),
                name="unique_course_rating_prompt",
            ),
        ]


class StaffMember(models.Model):
    class Role(models.TextChoices):
        PROFESSOR = "professeur", "Professeur"
        ADMIN = "admin", "Administrasyon"
        STAFF = "staff", "Ekip"

    name = models.CharField(max_length=120)
    role = models.CharField(max_length=16, choices=Role.choices)
    photo = models.ImageField(upload_to="staff/", blank=True)
    bio = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("display_order", "name")

    def __str__(self):
        return self.name
