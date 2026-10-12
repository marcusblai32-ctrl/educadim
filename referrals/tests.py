from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from courses.models import Course
from enrollments.models import Enrollment
from .models import (
    PointTransaction,
    Rating,
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
from .services import (
    calculate_discount,
    on_course_purchase,
    register_with_referral,
    request_withdrawal,
)

User = get_user_model()


class ReferralServiceTests(TestCase):
    def setUp(self):
        for key in (
            "referral_system",
            "points_system",
            "discount_system",
            "rating_system",
            "staff_carousel",
            "withdrawal_system",
        ):
            SystemFlag.objects.update_or_create(key=key, defaults={"is_active": True})
        self.referrer = User.objects.create_user(
            email="referrer@example.test",
            first_name="Ada",
            last_name="Learner",
            birth_year=1990,
            password="SecurePass!234",
        )
        self.referred = User.objects.create_user(
            email="referred@example.test",
            first_name="Sam",
            last_name="Learner",
            birth_year=1994,
            password="SecurePass!234",
        )
        self.course = Course.objects.create(titre="Django", prix=Decimal("200.00"))
        self.code = ReferralCode.objects.create(user=self.referrer, code="ADA2026")
        self.referral = Referral.objects.create(
            referrer=self.referrer,
            referred=self.referred,
            code_used=self.code.code,
        )

    def configure(self, **values):
        config = ReferralConfig.load()
        for field, value in values.items():
            setattr(config, field, value)
        config.save()
        return config

    def test_verified_paid_enrollment_awards_once(self):
        self.configure(
            reward_mode=ReferralConfig.RewardMode.BOTH,
            points_first_purchase=50,
            cash_percentage_first=Decimal("10.00"),
        )
        enrollment = Enrollment.objects.create(
            utilisateur=self.referred,
            cours=self.course,
            statut="pending",
            methode_paiement="moncash",
        )
        enrollment.statut = "active"
        enrollment.save(update_fields=("statut",))
        enrollment.save()

        balance = UserPoints.objects.get(user=self.referrer)
        self.assertEqual(balance.balance, 50)
        self.assertEqual(balance.cash_balance, Decimal("20.00"))
        self.assertEqual(
            ReferralReward.objects.filter(reference_id=enrollment.pk).count(), 1
        )
        self.assertEqual(PointTransaction.objects.filter(user=self.referrer).count(), 1)
        self.assertEqual(
            self.referral.__class__.objects.get(pk=self.referral.pk).status,
            "purchased",
        )

    def test_disabled_referral_flag_suppresses_reward_and_transaction(self):
        SystemFlag.objects.filter(key="referral_system").update(is_active=False)
        enrollment = Enrollment.objects.create(
            utilisateur=self.referred,
            cours=self.course,
            statut="pending",
            methode_paiement="natcash",
        )
        enrollment.statut = "active"
        enrollment.save(update_fields=("statut",))
        self.assertFalse(ReferralReward.objects.exists())
        self.assertFalse(PointTransaction.objects.exists())
        self.assertFalse(UserPoints.objects.exists())

    def test_points_flag_suppresses_points_even_when_cash_rewards_enabled(self):
        SystemFlag.objects.filter(key="points_system").update(is_active=False)
        self.configure(
            reward_mode=ReferralConfig.RewardMode.BOTH,
            points_first_purchase=50,
            cash_percentage_first=Decimal("5.00"),
        )
        reward = on_course_purchase(
            self.referred, self.course, Decimal("200.00"), reference_id=801
        )
        self.assertEqual(reward.points_awarded, 0)
        self.assertEqual(reward.cash_awarded, Decimal("10.00"))
        self.assertEqual(UserPoints.objects.get(user=self.referrer).balance, 0)
        self.assertEqual(
            UserPoints.objects.get(user=self.referrer).cash_balance,
            Decimal("10.00"),
        )
        self.assertEqual(PointTransaction.objects.get(user=self.referrer).amount, 0)

    def test_referral_registration_rejects_self_referral_and_awards_signup_points(self):
        self.configure(
            reward_mode=ReferralConfig.RewardMode.POINTS, points_signup=10
        )
        self.assertIsNone(register_with_referral(self.referrer, self.code.code))
        another_user = User.objects.create_user(
            email="new@example.test",
            first_name="New",
            last_name="Student",
            birth_year=2000,
            password="SecurePass!234",
        )
        result = register_with_referral(another_user, self.code.code)
        self.assertEqual(result.referred, another_user)
        self.assertEqual(UserPoints.objects.get(user=self.referrer).balance, 10)

    def test_discount_requires_both_flags_and_threshold(self):
        self.configure(
            discount_points_threshold=100, discount_percentage=Decimal("15.00")
        )
        UserPoints.objects.create(user=self.referred, balance=150)
        self.assertEqual(calculate_discount(self.referred), Decimal("15.00"))
        SystemFlag.objects.filter(key="points_system").update(is_active=False)
        self.assertEqual(calculate_discount(self.referred), Decimal("0.00"))

    def test_withdrawal_rejection_refunds_reserved_points(self):
        UserPoints.objects.create(user=self.referred, balance=500)
        RewardTier.objects.create(
            min_points=100, max_points=500, money_value=Decimal("40.00")
        )
        withdrawal = request_withdrawal(
            self.referred, 200, WithdrawalRequest.Method.MONCASH, "50912345678"
        )
        self.assertEqual(withdrawal.cash_amount, Decimal("40.00"))
        self.assertEqual(UserPoints.objects.get(user=self.referred).balance, 300)

        from .services import process_withdrawal
        process_withdrawal(
            withdrawal.pk, WithdrawalRequest.Status.REJECTED, self.referrer
        )
        points = UserPoints.objects.get(user=self.referred)
        self.assertEqual(points.balance, 500)
        self.assertEqual(points.total_withdrawn, 0)

    def test_cash_withdrawal_rejection_refunds_cash_balance(self):
        from .services import process_withdrawal, request_cash_withdrawal

        UserPoints.objects.create(
            user=self.referred, cash_balance=Decimal("90.00")
        )
        withdrawal = request_cash_withdrawal(
            self.referred, Decimal("50.00"), WithdrawalRequest.Method.NATCASH, "50912345678"
        )
        self.assertEqual(UserPoints.objects.get(user=self.referred).cash_balance, Decimal("40.00"))
        process_withdrawal(
            withdrawal.pk, WithdrawalRequest.Status.REJECTED, self.referrer
        )
        self.assertEqual(
            UserPoints.objects.get(user=self.referred).cash_balance,
            Decimal("90.00"),
        )

    def test_approved_withdrawal_updates_total_withdrawn(self):
        from .services import process_withdrawal

        UserPoints.objects.create(user=self.referred, balance=500)
        RewardTier.objects.create(
            min_points=100, max_points=500, money_value=Decimal("40.00")
        )
        withdrawal = request_withdrawal(
            self.referred, 200, WithdrawalRequest.Method.MONCASH, "50912345678"
        )
        self.assertEqual(UserPoints.objects.get(user=self.referred).total_withdrawn, 0)
        process_withdrawal(
            withdrawal.pk, WithdrawalRequest.Status.APPROVED, self.referrer
        )
        points = UserPoints.objects.get(user=self.referred)
        self.assertEqual(points.balance, 300)
        self.assertEqual(points.total_withdrawn, 200)


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class FeatureFlagViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="student@example.test",
            first_name="Test",
            last_name="Student",
            birth_year=2001,
            password="SecurePass!234",
        )
        SystemFlag.objects.update_or_create(
            key="points_system", defaults={"is_active": False}
        )

    def test_points_page_returns_404_when_feature_is_disabled(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("referrals:my_points"))
        self.assertEqual(response.status_code, 404)

    def test_student_reward_pages_render(self):
        SystemFlag.objects.filter(key="points_system").update(is_active=True)
        self.client.force_login(self.user)
        for name in (
            "referrals:my_points",
            "referrals:my_referrals",
            "referrals:withdrawal",
        ):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_admin_can_save_feature_flags(self):
        self.user.is_staff = True
        self.user.save(update_fields=("is_staff",))
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("referrals:admin_flags"),
            {
                "flag_referral_system": "on",
                "flag_points_system": "on",
                "flag_discount_system": "on",
                "flag_rating_system": "on",
                "flag_staff_carousel": "on",
                "flag_withdrawal_system": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SystemFlag.objects.get(key="points_system").is_active)

    def test_rating_submission_stays_pending_until_approved(self):
        SystemFlag.objects.update_or_create(
            key="rating_system", defaults={"is_active": True}
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("referrals:submit_rating"),
            {"stars": 5, "comment": "Excellent", "next": reverse("home")},
        )
        self.assertEqual(response.status_code, 302)
        rating = Rating.objects.get(user=self.user)
        self.assertFalse(rating.is_approved)

    def test_home_shows_only_approved_ratings_and_active_staff_when_enabled(self):
        Rating.objects.create(
            user=self.user, stars=5, comment="Bon suivi.", is_approved=True
        )
        StaffMember.objects.create(name="Prof Test", role=StaffMember.Role.PROFESSOR)

        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bon suivi.")
        self.assertContains(response, "Prof Test")

        SystemFlag.objects.filter(key="rating_system").update(is_active=False)
        SystemFlag.objects.filter(key="staff_carousel").update(is_active=False)
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Bon suivi.")
        self.assertNotContains(response, "Prof Test")

    def test_course_card_uses_theme_discount_only_when_flags_are_active(self):
        from .models import ReferralConfig

        SystemFlag.objects.filter(key="points_system").update(is_active=True)
        config = ReferralConfig.load()
        config.discount_points_threshold = 100
        config.discount_percentage = Decimal("15.00")
        config.save()
        UserPoints.objects.create(user=self.user, balance=100)
        course = Course.objects.create(
            titre="Cours remisé", prix=Decimal("200.00"), publie=True
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("courses:course_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["cours"]), 1)
        self.assertEqual(
            response.context["cours"][0]["discount_percent"], Decimal("15.00")
        )
        self.assertEqual(
            response.context["cours"][0]["discounted_price"], Decimal("170.00")
        )
        self.assertContains(response, "-15%")

        enrollment_response = self.client.get(
            reverse("enrollments:enroll_course", args=(course.pk,))
        )
        self.assertEqual(enrollment_response.status_code, 200)
        self.assertEqual(
            enrollment_response.context["payment_due"], Decimal("170.00")
        )

        SystemFlag.objects.filter(key="discount_system").update(is_active=False)
        response = self.client.get(reverse("courses:course_list"))
        self.assertNotContains(response, "-15%")
        self.assertEqual(
            response.context["cours"][0]["discounted_price"], Decimal("200.00")
        )

    def test_new_admin_screens_render(self):
        self.user.is_staff = True
        self.user.save(update_fields=("is_staff",))
        self.client.force_login(self.user)
        names = (
            "referrals:admin_flags",
            "referrals:admin_config",
            "referrals:admin_tiers",
            "referrals:admin_withdrawals",
            "referrals:admin_transactions",
            "referrals:admin_referrals",
            "referrals:admin_staff",
        )
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

