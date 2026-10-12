from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    RatingForm,
    ReferralConfigForm,
    RewardTierForm,
    WithdrawalRequestForm,
)
from .models import (
    PointTransaction,
    Rating,
    RatingPrompt,
    Referral,
    ReferralCode,
    ReferralConfig,
    RewardTier,
    StaffMember,
    SystemFlag,
    UserPoints,
    WithdrawalRequest,
)
from .services import (
    SYSTEM_KEYS,
    get_all_referrals,
    get_or_create_referral_code,
    get_referral_stats,
    is_system_active,
    process_withdrawal,
    request_cash_withdrawal,
    request_withdrawal,
    track_click,
)


def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def _require_flag(key):
    if not is_system_active(key):
        raise Http404


def _safe_next(request, fallback):
    destination = request.POST.get("next", "")
    if destination and url_has_allowed_host_and_scheme(
        destination,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return destination
    return fallback


def referral_link(request, code):
    referral_code = track_click(code)
    if not referral_code:
        raise Http404
    request.session["referral_code"] = referral_code.code
    if request.user.is_authenticated:
        return redirect("home")
    return redirect("accounts:signup")


@login_required
def my_points(request):
    _require_flag("points_system")
    points, _ = UserPoints.objects.get_or_create(user=request.user)
    transactions = PointTransaction.objects.filter(user=request.user)
    referral = None
    referral_url = None
    if is_system_active("referral_system"):
        referral = get_or_create_referral_code(request.user)
        referral_url = request.build_absolute_uri(
            reverse("referrals:track", kwargs={"code": referral.code})
        )
    config = ReferralConfig.load()
    return render(request, "referrals/user/my_points.html", {
        "points": points,
        "transactions": transactions[:50],
        "referral_code": referral,
        "referral_url": referral_url,
        "can_withdraw": (
            is_system_active("withdrawal_system")
            and (
                (
                    is_system_active("points_system")
                    and points.balance >= config.minimum_withdrawal_points
                )
                or (
                    is_system_active("referral_system")
                    and points.cash_balance > 0
                )
            )
        ),
        "stats": get_referral_stats(request.user),
    })


@login_required
def my_referrals(request):
    _require_flag("referral_system")
    referrals = (
        Referral.objects.filter(referrer=request.user)
        .select_related("referred")
        .prefetch_related("rewards")
    )
    return render(request, "referrals/user/my_referrals.html", {
        "referrals": referrals,
        "stats": get_referral_stats(request.user),
    })


@login_required
def withdrawal_request(request):
    _require_flag("withdrawal_system")
    form = WithdrawalRequestForm(request.POST or None)
    withdrawal_choices = []
    if is_system_active("points_system"):
        withdrawal_choices.append(("points", "Pwen"))
    if is_system_active("referral_system"):
        withdrawal_choices.append(("cash", "Lajan deja kredite"))
    if not withdrawal_choices:
        raise Http404
    form.fields["withdrawal_type"].choices = withdrawal_choices
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["withdrawal_type"] == "points":
            if not is_system_active("points_system"):
                raise Http404
            withdrawal = request_withdrawal(
                request.user,
                int(form.cleaned_data["amount"]),
                form.cleaned_data["method"],
                form.cleaned_data["destination"],
            )
        else:
            withdrawal = request_cash_withdrawal(
                request.user,
                form.cleaned_data["amount"],
                form.cleaned_data["method"],
                form.cleaned_data["destination"],
            )
        if withdrawal is None:
            form.add_error("amount", "Balans lan pa sifi, oswa pa gen nivo konvèsyon aktif.")
        else:
            messages.success(request, "Demann retrè a voye pou verifikasyon.")
            if is_system_active("points_system"):
                return redirect("referrals:my_points")
            return redirect("home")
    points = UserPoints.objects.filter(user=request.user).first()
    return render(request, "referrals/user/withdrawal.html", {
        "form": form,
        "available_points": points.balance if points and is_system_active("points_system") else 0,
        "available_cash": points.cash_balance if points and is_system_active("referral_system") else Decimal("0.00"),
    })


@user_passes_test(is_admin)
def system_toggle(request):
    if request.method == "POST":
        for key in SYSTEM_KEYS:
            active = request.POST.get(f"flag_{key}") == "on"
            SystemFlag.objects.update_or_create(
                key=key, defaults={"is_active": active}
            )
        messages.success(request, "Aktivasyon fonksyonalite yo mete ajou.")
        return redirect("referrals:admin_flags")
    stored = dict(SystemFlag.objects.values_list("key", "is_active"))
    flags = [{"key": key, "is_active": stored.get(key, True)} for key in SYSTEM_KEYS]
    return render(request, "referrals/admin/system_toggle.html", {"system_flags": flags})


@user_passes_test(is_admin)
def referral_config(request):
    config = ReferralConfig.load()
    form = ReferralConfigForm(request.POST or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Konfigirasyon rekonpans lan sove.")
        return redirect("referrals:admin_config")
    return render(request, "referrals/admin/config.html", {"form": form})


@user_passes_test(is_admin)
def reward_tiers(request):
    form = RewardTierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Nivo rekonpans lan ajoute.")
        return redirect("referrals:admin_tiers")
    return render(request, "referrals/admin/tiers.html", {
        "tiers": RewardTier.objects.all(),
        "form": form,
    })


@user_passes_test(is_admin)
def reward_tier_edit(request, pk):
    tier = get_object_or_404(RewardTier, pk=pk)
    form = RewardTierForm(request.POST or None, instance=tier)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Nivo rekonpans lan mete ajou.")
        return redirect("referrals:admin_tiers")
    return render(request, "referrals/admin/tier_edit.html", {"form": form, "tier": tier})


@user_passes_test(is_admin)
@require_POST
def reward_tier_delete(request, pk):
    get_object_or_404(RewardTier, pk=pk).delete()
    messages.success(request, "Nivo rekonpans lan efase.")
    return redirect("referrals:admin_tiers")


@user_passes_test(is_admin)
def withdrawal_list(request):
    withdrawals = WithdrawalRequest.objects.select_related("user", "processed_by")
    return render(request, "referrals/admin/withdrawals.html", {"withdrawals": withdrawals})


@user_passes_test(is_admin)
@require_POST
def withdrawal_process(request, pk, action):
    status = {
        "approve": WithdrawalRequest.Status.APPROVED,
        "reject": WithdrawalRequest.Status.REJECTED,
    }.get(action)
    if status is None:
        raise Http404
    try:
        withdrawal = process_withdrawal(pk, status, request.user)
    except WithdrawalRequest.DoesNotExist:
        raise Http404
    if withdrawal is None:
        messages.error(request, "Sistèm retrè a dezaktive; pa gen aksyon ki fèt.")
    else:
        messages.success(request, f"Demann {withdrawal.pk} la trete.")
    return redirect("referrals:admin_withdrawals")


@user_passes_test(is_admin)
def all_transactions(request):
    page = Paginator(
        PointTransaction.objects.select_related("user"), 50
    ).get_page(request.GET.get("page"))
    return render(request, "referrals/admin/transactions.html", {"page_obj": page})


@user_passes_test(is_admin)
def all_referrals(request):
    from .models import Referral
    page = Paginator(get_all_referrals(request.GET), 50).get_page(request.GET.get("page"))
    return render(request, "referrals/admin/referrals.html", {
        "page_obj": page,
        "statuses": Referral.Status.choices,
    })


@login_required
@require_POST
def submit_rating(request):
    _require_flag("rating_system")
    form = RatingForm(request.POST)
    if form.is_valid():
        rating = form.save(commit=False)
        rating.user = request.user
        course_id = request.POST.get("course")
        if course_id:
            from courses.models import Course
            rating.course = get_object_or_404(Course, pk=course_id)
        rating.save()
        messages.success(request, "Mèsi! N ap verifye evalyasyon ou anvan li parèt.")
    else:
        messages.error(request, "Tanpri chwazi yon nòt valab.")
    return redirect(_safe_next(request, "home"))


@login_required
@require_POST
def mark_rating_prompt(request):
    _require_flag("rating_system")
    course_id = request.POST.get("course")
    if course_id:
        from courses.models import Course
        course = get_object_or_404(Course, pk=course_id)
        prompt, created = RatingPrompt.objects.get_or_create(
            user=request.user, course=course, defaults={"shown": True}
        )
        if not created and not prompt.shown:
            prompt.shown = True
            prompt.save(update_fields=("shown",))
    elif not RatingPrompt.objects.filter(
        user=request.user, course__isnull=True, shown=True
    ).exists():
        RatingPrompt.objects.create(user=request.user, shown=True)
    return JsonResponse({"recorded": True})


@user_passes_test(is_admin)
@require_POST
def approve_rating(request, pk):
    if not is_system_active("rating_system"):
        raise Http404
    rating = get_object_or_404(Rating, pk=pk)
    rating.is_approved = request.POST.get("approved") == "true"
    rating.save(update_fields=("is_approved",))
    return redirect(_safe_next(request, "admin:index"))


@user_passes_test(is_admin)
def staff_members(request):
    return render(request, "referrals/admin/staff.html", {
        "staff_members": StaffMember.objects.all(),
        "admin_url": reverse("admin:referrals_staffmember_changelist"),
    })
