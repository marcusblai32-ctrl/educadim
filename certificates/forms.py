from django import forms
from django.core.exceptions import ValidationError

from .models import Certificate, CertificateSigner


class CertificateRequestForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ("student_name", "student_note")
        widgets = {
            "student_name": forms.TextInput(
                attrs={"class": "form-control", "autocomplete": "name", "maxlength": 180}
            ),
            "student_note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Précisez la correction demandée, si nécessaire.",
                }
            ),
        }
        labels = {
            "student_name": "Nom complet à imprimer",
            "student_note": "Précision ou correction (facultatif)",
        }


class CertificateReviewForm(forms.Form):
    decision = forms.ChoiceField(
        choices=(
            ("issue", "Vérifier et envoyer le certificat"),
            ("correction", "Demander une correction à l'étudiant"),
        ),
        widget=forms.RadioSelect,
        label="Décision",
    )
    student_name = forms.CharField(
        max_length=180,
        label="Nom à imprimer",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    review_note = forms.CharField(
        required=False,
        label="Note à l'étudiant / note interne",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
    )
    signers = forms.ModelMultipleChoiceField(
        queryset=CertificateSigner.objects.none(),
        required=False,
        label="Signataires dynamiques",
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["signers"].queryset = CertificateSigner.objects.filter(
            is_active=True
        )

    def clean(self):
        cleaned_data = super().clean()
        decision = cleaned_data.get("decision")
        selected_signers = cleaned_data.get("signers")
        if decision == "issue" and not selected_signers:
            self.add_error(
                "signers",
                ValidationError("Sélectionnez au moins un signataire actif."),
            )
        if selected_signers and selected_signers.count() > 4:
            self.add_error(
                "signers",
                ValidationError("Sélectionnez quatre signataires au maximum."),
            )
        if decision == "correction" and not (
            cleaned_data.get("review_note") or ""
        ).strip():
            self.add_error(
                "review_note",
                ValidationError("Expliquez à l'étudiant la correction nécessaire."),
            )
        return cleaned_data


class CertificateRevokeForm(forms.Form):
    review_note = forms.CharField(
        label="Motif de révocation",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )
