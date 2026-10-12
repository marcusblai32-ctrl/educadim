from django import forms
from django.core.exceptions import ValidationError

from .models import Rating, ReferralConfig, RewardTier, StaffMember, WithdrawalRequest


class ReferralConfigForm(forms.ModelForm):
    class Meta:
        model = ReferralConfig
        exclude = ()
        widgets = {
            "cash_percentage_first": forms.NumberInput(attrs={"step": "0.01"}),
            "cash_percentage_repeat": forms.NumberInput(attrs={"step": "0.01"}),
            "discount_percentage": forms.NumberInput(attrs={"step": "0.01"}),
        }


class RewardTierForm(forms.ModelForm):
    class Meta:
        model = RewardTier
        fields = ("min_points", "max_points", "money_value", "is_active")

    def clean(self):
        cleaned = super().clean()
        minimum = cleaned.get("min_points")
        maximum = cleaned.get("max_points")
        if minimum is not None and maximum is not None and minimum <= maximum:
            overlaps = RewardTier.objects.filter(
                min_points__lte=maximum,
                max_points__gte=minimum,
            )
            if self.instance.pk:
                overlaps = overlaps.exclude(pk=self.instance.pk)
            if overlaps.exists():
                raise ValidationError(
                    "Ranje sa a sipèpoze ak yon lòt nivo pwen ki deja egziste."
                )
        return cleaned


class WithdrawalRequestForm(forms.Form):
    withdrawal_type = forms.ChoiceField(
        choices=(("points", "Pwen"), ("cash", "Lajan deja kredite")),
        label="Kalite retrè",
    )
    amount = forms.DecimalField(
        min_value=1,
        decimal_places=2,
        max_digits=12,
        label="Montan pwen oswa HTG",
        widget=forms.NumberInput(attrs={"step": "1", "min": "1"}),
    )
    method = forms.ChoiceField(choices=WithdrawalRequest.Method.choices)
    destination = forms.CharField(
        max_length=160, widget=forms.TextInput(attrs={"autocomplete": "off"})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("withdrawal_type") == "points":
            amount = cleaned.get("amount")
            if amount is not None and amount != amount.to_integral_value():
                self.add_error("amount", "Pou retrè pwen, montan an dwe yon nonb antye.")
        return cleaned


class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ("stars", "comment")
        widgets = {
            "stars": forms.RadioSelect(),
            "comment": forms.Textarea(attrs={"rows": 3, "maxlength": 1500}),
        }


class StaffMemberForm(forms.ModelForm):
    class Meta:
        model = StaffMember
        fields = ("name", "role", "photo", "bio", "display_order", "is_active")
