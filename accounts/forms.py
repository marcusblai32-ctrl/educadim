from django import forms
from django.contrib.auth.forms import PasswordResetForm, UserCreationForm
from django.urls import reverse

from utils.notifications import send_password_reset
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'birth_year', 'password1', 'password2')
        labels = {
            'email': 'Email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'birth_year': 'Année de naissance',
        }
        widgets = {
            'birth_year': forms.NumberInput(attrs={'min': 1900, 'max': 2026}),
        }

    def clean_birth_year(self):
        year = self.cleaned_data.get('birth_year')
        import datetime
        current_year = datetime.datetime.now().year
        if year < 1900 or year > current_year:
            raise forms.ValidationError("Année de naissance invalide.")
        return year


class CustomPasswordResetForm(PasswordResetForm):
    """Deliver Django's secure password-reset link by email and SMS."""

    def send_mail(
        self,
        subject_template_name,
        email_template_name,
        context,
        from_email,
        to_email,
        html_email_template_name=None,
    ):
        user = context.get("user")
        if user is None:
            return

        reset_path = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": context["uid"], "token": context["token"]},
        )
        reset_link = f"{context['protocol']}://{context['domain']}{reset_path}"

        send_password_reset(
            user,
            reset_link,
            send_email=bool(user.email),
            send_sms=bool(getattr(user, "phone_number", None)),
        )
