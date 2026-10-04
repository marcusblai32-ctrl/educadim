from django.contrib.auth.backends import BaseBackend

from .models import CustomUser


class UserIDBackend(BaseBackend):
    """Konekte ak user_id. Refize kont ki pa aktif (menm règ ak ModelBackend)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        try:
            user = CustomUser.objects.get(user_id=username)
        except CustomUser.DoesNotExist:
            # Menm travay lè itilizatè a pa egziste, pou evite timing attack
            CustomUser().set_password(password)
            return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
        return user if user.is_active else None