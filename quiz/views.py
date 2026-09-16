import os
import mimetypes
from django.http import FileResponse, Http404, HttpResponseForbidden


# ============================================
# VIEWS SEKIRIZE POU MEDIA
# ============================================

def _user_can_access_reponse(user, reponse):
    """Verifye si itilizatè a gen dwa wè repons lan."""
    if not user.is_authenticated:
        return False
    # Mèt repons lan
    if reponse.tentative.utilisateur_id == user.id:
        return True
    # Staff oswa admin
    if user.is_staff or user.is_superuser:
        return True
    # Enstriktè (si w gen yon flag)
    if getattr(user, 'is_instructor', False):
        return True
    return False


@login_required
def serve_audio_reponse(request, reponse_id):
    """Sèvi odyo yon repons ak verifikasyon otorizasyon."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)

    if not _user_can_access_reponse(request.user, reponse):
        return HttpResponseForbidden("Ou pa gen dwa wè fichye sa a.")

    if not reponse.audio_reponse:
        raise Http404("Fichye pa egziste.")

    file_path = reponse.audio_reponse.path
    if not os.path.exists(file_path):
        raise Http404("Fichye pa egziste sou sèvè a.")

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
    """Sèvi video yon repons ak verifikasyon otorizasyon."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)

    if not _user_can_access_reponse(request.user, reponse):
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
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'

    return response


@login_required
def serve_image_reponse(request, reponse_id):
    """Sèvi imaj yon repons ak verifikasyon otorizasyon."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)

    if not _user_can_access_reponse(request.user, reponse):
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
    """Sèvi fichye yon repons ak verifikasyon otorizasyon."""
    reponse = get_object_or_404(ReponseUtilisateur, pk=reponse_id)

    if not _user_can_access_reponse(request.user, reponse):
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