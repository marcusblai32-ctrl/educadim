import os
import mimetypes

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext as _
from django.http import JsonResponse, FileResponse, Http404, HttpResponseForbidden
from django.contrib.admin.views.decorators import staff_member_required

from .models import Quiz, Question, Reponse, TentativeQuiz, ReponseUtilisateur
from .services import corriger_tentative, get_upload_fields_for_question


# ============================================
# VIEWS PIBLIK
# ============================================

def quiz_list(request):
    """Lis tout quiz pibliye yo."""
    quizzes = Quiz.objects.filter(publie=True)
    return render(request, 'quiz/list.html', {'quizzes': quizzes})


def quiz_detail(request, pk):
    """Detay yon quiz."""
    quiz = get_object_or_404(Quiz, pk=pk)
    return render(request, 'quiz/detail.html', {'quiz': quiz})


@login_required
def start_quiz(request, pk):
    """Kòmanse yon quiz."""
    quiz = get_object_or_404(Quiz, pk=pk)
    tentative = TentativeQuiz.objects.filter(
        utilisateur=request.user,
        quiz=quiz,
        date_soumission__isnull=True,
    ).first()
    if not tentative:
        tentative = TentativeQuiz.objects.create(utilisateur=request.user, quiz=quiz)
    return redirect('quiz:take_quiz', tentative_pk=tentative.pk)


@login_required
def take_quiz(request, tentative_pk):
    """Paj pou reponn yon quiz."""
    tentative = get_object_or_404(TentativeQuiz, pk=tentative_pk, utilisateur=request.user)

    if tentative.date_soumission:
        messages.warning(request, _("Ce quiz a déjà été soumis."))
        return redirect('quiz:quiz_result', tentative_pk=tentative.pk)

    questions = tentative.quiz.questions.all().order_by('ordre')
    total_questions = questions.count()

    reponses_utilisateur = {
        ru.question_id: ru
        for ru in ReponseUtilisateur.objects.filter(tentative=tentative)
    }

    quiz_duree = tentative.quiz.duree_quiz if tentative.quiz.duree_quiz else 15

    return render(request, 'quiz/take_quiz.html', {
        'tentative': tentative,
        'questions': questions,
        'total_questions': total_questions,
        'reponses_utilisateur': reponses_utilisateur,
        'quiz_duree': quiz_duree,
    })


@login_required
def submit_quiz(request, tentative_pk):
    """Soumèt repons yo."""
    tentative = get_object_or_404(TentativeQuiz, pk=tentative_pk, utilisateur=request.user)

    if tentative.date_soumission:
        messages.warning(request, _("Ce quiz a déjà été soumis."))
        return redirect('quiz:quiz_result', tentative_pk=tentative.pk)

    if request.method == 'POST':
        print("=" * 60)
        print("=== FILES keys ===", list(request.FILES.keys()))
        print("=== POST keys ===", list(request.POST.keys()))
        for key in request.FILES:
            f = request.FILES[key]
            print(f"  FILES['{key}'] = {f.name} ({f.size} bytes) | type: {f.content_type}")
        print("=" * 60)

        questions = tentative.quiz.questions.all()

        for question in questions:
            reponse_utilisateur, created = ReponseUtilisateur.objects.get_or_create(
                tentative=tentative, question=question
            )

            if question.type_question in ['single', 'vrai_faux']:
                reponse_id = request.POST.get(f'question_{question.id}')
                if reponse_id:
                    reponse = get_object_or_404(Reponse, pk=reponse_id)
                    reponse_utilisateur.reponses_selectionnees.set([reponse])
                else:
                    reponse_utilisateur.reponses_selectionnees.clear()

            elif question.type_question == 'multiple':
                reponse_ids = request.POST.getlist(f'question_{question.id}')
                if reponse_ids:
                    reponses = Reponse.objects.filter(pk__in=reponse_ids)
                    reponse_utilisateur.reponses_selectionnees.set(reponses)
                else:
                    reponse_utilisateur.reponses_selectionnees.clear()

            elif question.type_question == 'texte_trous':
                reponse_utilisateur.texte_reponse = request.POST.get(
                    f'question_{question.id}_texte', ''
                ).strip()

            elif question.type_question == 'texte_libre':
                reponse_utilisateur.texte_reponse = request.POST.get(
                    f'question_{question.id}_texte_libre', ''
                ).strip()

            elif question.type_question == 'audio_reponse':
                fichye = (
                    request.FILES.get(f'question_{question.id}_audio') or
                    request.FILES.get(f'question_{question.id}_audio_upload')
                )
                if fichye and fichye.size > 0:
                    reponse_utilisateur.audio_reponse = fichye
                    print(f"✅ Audio rive: {fichye.name} ({fichye.size} bytes) pou Q{question.id}")
                elif fichye:
                    print(f"❌ FICHYE VID pou Q{question.id}!")
                else:
                    print(f"❌ PA GEN audio pou Q{question.id}")

            elif question.type_question == 'video_reponse':
                fichye = request.FILES.get(f'question_{question.id}_video')
                if fichye and fichye.size > 0:
                    reponse_utilisateur.video_reponse = fichye
                    print(f"✅ Video rive: {fichye.name} ({fichye.size} bytes)")

            elif question.type_question == 'image_reponse':
                fichye = request.FILES.get(f'question_{question.id}_image')
                if fichye and fichye.size > 0:
                    reponse_utilisateur.image_reponse = fichye
                    print(f"✅ Image rive: {fichye.name} ({fichye.size} bytes)")

            elif question.type_question == 'fichier_reponse':
                fichye = request.FILES.get(f'question_{question.id}_fichier')
                if fichye and fichye.size > 0:
                    reponse_utilisateur.fichier_reponse = fichye
                    print(f"✅ Fichye rive: {fichye.name} ({fichye.size} bytes)")

            reponse_utilisateur.save()

        corriger_tentative(tentative)
        messages.success(request, _("Quiz soumis avec succès!"))
        return redirect('quiz:quiz_result', tentative_pk=tentative.pk)

    return redirect('quiz:take_quiz', tentative_pk=tentative.pk)


@login_required
def quiz_result(request, tentative_pk):
    """Montre rezilta yon quiz."""
    tentative = get_object_or_404(TentativeQuiz, pk=tentative_pk, utilisateur=request.user)

    if not tentative.date_soumission:
        messages.warning(request, _("Vous n'avez pas encore soumis ce quiz."))
        return redirect('quiz:take_quiz', tentative_pk=tentative.pk)

    reponses_utilisateur = ReponseUtilisateur.objects.filter(
        tentative=tentative
    ).select_related('question')

    return render(request, 'quiz/result.html', {
        'tentative': tentative,
        'reponses_utilisateur': reponses_utilisateur,
    })


def get_question_upload_type(request, question_id):
    """API pou jwenn tip upload yon kesyon."""
    question = get_object_or_404(Question, pk=question_id)
    upload_info = get_upload_fields_for_question(question)
    if upload_info:
        return JsonResponse(upload_info)
    return JsonResponse({'error': 'Not an upload type'}, status=400)


# ============================================
# VIEWS KOREKSYON STAFF
# ============================================

@staff_member_required
def tentative_list(request):
    """Lis tout tantativ pou koreksyon."""
    tentatives = TentativeQuiz.objects.filter(
        date_soumission__isnull=False
    ).select_related('utilisateur', 'quiz')
    return render(request, 'quiz/correction/tentative_list.html', {'tentatives': tentatives})


@staff_member_required
def corriger_tentative_view(request, tentative_pk):
    """Koreksyon yon tantativ."""
    tentative = get_object_or_404(
        TentativeQuiz, pk=tentative_pk, date_soumission__isnull=False
    )
    questions = tentative.quiz.questions.all().order_by('ordre')
    reponses_utilisateur = ReponseUtilisateur.objects.filter(
        tentative=tentative
    ).select_related('question')

    if request.method == 'POST':
        for ru in reponses_utilisateur:
            points_key = f'points_{ru.id}'
            if points_key in request.POST:
                val = request.POST[points_key].strip()
                ru.points_attribues = float(val) if val else None
                ru.save()
        corriger_tentative(tentative)
        messages.success(request, _("Koreksyon anrejistre epi nòt rekalkile."))
        return redirect('quiz:corriger_tentative', tentative_pk=tentative.pk)

    question_data = []
    for q in questions:
        ru = next((r for r in reponses_utilisateur if r.question_id == q.id), None)
        selected_reponses = ru.reponses_selectionnees.all() if ru else []
        upload_fields = {
            'audio': ru.audio_reponse if ru else None,
            'video': ru.video_reponse if ru else None,
            'image': ru.image_reponse if ru else None,
            'fichier': ru.fichier_reponse if ru else None,
            'texte': ru.texte_reponse if ru else None,
        }
        question_data.append({
            'question': q,
            'reponse_utilisateur': ru,
            'selected_reponses': selected_reponses,
            'upload_fields': upload_fields,
        })

    return render(request, 'quiz/correction/corriger_tentative.html', {
        'tentative': tentative,
        'question_data': question_data,
    })


# ============================================
# VIEWS SEKIRIZE POU MEDIA
# ============================================

def _user_can_access_reponse(user, reponse):
    """Verifye si itilizatè a gen dwa wè repons lan."""
    if not user.is_authenticated:
        return False
    if reponse.tentative.utilisateur_id == user.id:
        return True
    if user.is_staff or user.is_superuser:
        return True
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