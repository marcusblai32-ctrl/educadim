from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from .forms import CustomUserCreationForm
from .models import CustomUser
from django.contrib.auth import authenticate


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, _("Compte cree avec succes ! Votre ID est : ") + user.user_id)
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            user.update_activity()
            login(request, user)
            return redirect('accounts:profile')
        else:
            messages.error(request, _("Email/ID ou mot de passe incorrect."))
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    # Koreksyon: itilize 'accounts:login' olye de 'login'
    return redirect('accounts:login')

@login_required
def profile_view(request):
    request.user.update_activity()
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def delete_account(request):
    if request.method == 'POST':
        password = request.POST.get('password')
        if request.user.check_password(password):
            request.user.delete()
            logout(request)
            messages.success(request, "Votre compte a été supprimé avec succès.")
            return redirect('home')
        else:
            messages.error(request, "Mot de passe incorrect.")
            return redirect('accounts:profile')
    return render(request, 'accounts/delete_account.html')