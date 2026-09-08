from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('inscription/', views.signup_view, name='signup'),
    path('connexion/', views.login_view, name='login'),
    path('deconnexion/', views.logout_view, name='logout'),
    path('profil/', views.profile_view, name='profile'),
    path('supprimer/', views.delete_account, name='delete_account'),

    # Password Reset - AVEC success_url
    path('mot-de-passe-oublie/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
             success_url='done/',  # <-- AJOUTE SA
         ),
         name='password_reset'),

    path('mot-de-passe-oublie/done/',  # <-- AJOUTE SLASH LA
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reinitialiser/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url='complete/',  # <-- AJOUTE SA
         ),
         name='password_reset_confirm'),

    path('reinitialiser/complete/',  # <-- AJOUTE SLASH LA
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),
]