from django import forms
from .models import Course

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'titre', 'description', 'titre_ht', 'description_ht',
            'image_url', 'image',
            'prix', 'publie', 'categorie', 'nivo',
            'duree', 'date_debut_inscription', 'date_fin_inscription',
            'inscription_ouverte', 'learning_path', 'position'
        ]
        widgets = {
            'date_debut_inscription': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_fin_inscription': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'duree': forms.NumberInput(attrs={'min': 0}),
            'description': forms.Textarea(attrs={'rows': 5}),
            'description_ht': forms.Textarea(attrs={'rows': 5}),
            'position': forms.NumberInput(attrs={'min': 0}),
        }