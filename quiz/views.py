import os
import mimetypes
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import ReponseUtilisateur, TentativeQuiz


@login_required
def serve_audio_reponse(request, reponse_id):
    """
    Sèvi yon odyo repons ak verifikasyon otorizasyon.
    Sèlman mèt repons lan, pwofesè yo, ak admin yo ka aksede l.
    """
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)

    # ===== VERIFYE OTORIZASYON =====
    user = request.user
    is_owner = (reponse.tentative.utilisateur == user)
    is_staff = user.is_staff
    is_instructor = getattr(user, 'is_instructor', False)  # si ou gen sa

    if not (is_owner or is_staff or is_instructor):
        return HttpResponseForbidden("Ou pa gen dwa wè fichye sa a.")

    # ===== VERIFYE FICHYE A EGZISTE =====
    if not reponse.audio_reponse:
        raise Http404("Fichye pa egziste.")

    file_path = reponse.audio_reponse.path
    if not os.path.exists(file_path):
        raise Http404("Fichye pa egziste sou sèvè a.")

    # ===== SÈVI FICHYE A AK RANGE SUPPORT =====
    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'audio/webm'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Length'] = os.path.getsize(file_path)
    response['Accept-Ranges'] = 'bytes'
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'

    return response


@login_required
def serve_video_reponse(request, reponse_id):
    """Menm jan pou video."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)
    user = request.user

    if not (reponse.tentative.utilisateur == user or user.is_staff or getattr(user, 'is_instructor', False)):
        return HttpResponseForbidden("Ou pa gen dwa wè fichye sa a.")

    if not reponse.video_reponse:
        raise Http404("Fichye pa egziste.")

    file_path = reponse.video_reponse.path
    if not os.path.exists(file_path):
        raise Http404("Fichye pa egziste.")

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'video/webm'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Length'] = os.path.getsize(file_path)
    response['Accept-Ranges'] = 'bytes'

    return response


@login_required
def serve_image_reponse(request, reponse_id):
    """Menm jan pou imaj."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)
    user = request.user

    if not (reponse.tentative.utilisateur == user or user.is_staff or getattr(user, 'is_instructor', False)):
        return HttpResponseForbidden("Ou pa gen dwa wè fichye sa a.")

    if not reponse.image_reponse:
        raise Http404("Fichye pa egziste.")

    file_path = reponse.image_reponse.path
    if not os.path.exists(file_path):
        raise Http404("Fichye pa egziste.")

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'image/jpeg'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Length'] = os.path.getsize(file_path)

    return response


@login_required
def serve_fichier_reponse(request, reponse_id):
    """Menm jan pou fichye."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)
    user = request.user

    if not (reponse.tentative.utilisateur == user or user.is_staff or getattr(user, 'is_instructor', False)):
        return HttpResponseForbidden("Ou pa gen dwa wè fichye sa a.")

    if not reponse.fichier_reponse:
        raise Http404("Fichye pa egziste.")

    file_path = reponse.fichier_reponse.path
    if not os.path.exists(file_path):
        raise Http404("Fichye pa egziste.")

    content_type, _ = mimetypes.guess_type(file_path)
    if not content_type:
        content_type = 'application/octet-stream'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Length'] = os.path.getsize(file_path)

    return response