from django.utils import timezone
from .models import ReponseUtilisateur


def corriger_tentative(tentative):
    total_points = 0
    points_obtenus = 0.0

    for question in tentative.quiz.questions.all():
        total_points += question.points

        try:
            reponse_utilisateur = ReponseUtilisateur.objects.get(tentative=tentative, question=question)
        except ReponseUtilisateur.DoesNotExist:
            continue

        # ===== Si gen pwen manyèl, itilize yo =====
        if reponse_utilisateur.points_attribues is not None:
            points_obtenus += float(reponse_utilisateur.points_attribues)
            continue

        # ===== TYPES AVEC REPONSES (CHOIX) =====
        if question.type_question in ['single', 'vrai_faux']:
            bonne_reponse = question.reponses.filter(est_correcte=True).first()
            if bonne_reponse and reponse_utilisateur.reponses_selectionnees.filter(pk=bonne_reponse.pk).exists():
                points_obtenus += question.points

        elif question.type_question == 'multiple':
            bonnes_reponses = set(question.reponses.filter(est_correcte=True).values_list('pk', flat=True))
            reponses_selectionnees = set(reponse_utilisateur.reponses_selectionnees.values_list('pk', flat=True))
            if bonnes_reponses == reponses_selectionnees:
                points_obtenus += question.points

        elif question.type_question == 'texte_trous':
            bonne_reponse = question.reponses.first()
            if bonne_reponse and reponse_utilisateur.texte_reponse.strip().lower() == bonne_reponse.texte.strip().lower():
                points_obtenus += question.points

        # ===== TYPES AVEC UPLOAD (koreksyon manyèl) =====
        elif question.type_question in ['audio_reponse', 'video_reponse', 'image_reponse', 'fichier_reponse', 'texte_libre']:
            # Pa gen pwen otomatik — prof la dwe koreje manyèlman
            pass

    pourcentage = (points_obtenus / total_points * 100) if total_points > 0 else 0
    tentative.score = pourcentage
    tentative.reussi = pourcentage >= tentative.quiz.pourcentage_reussite
    tentative.date_soumission = timezone.now()
    tentative.save()
    return pourcentage


def get_upload_fields_for_question(question):
    """Retounen enfòmasyon sou champs upload selon tip kesyon an."""
    mapping = {
        'audio_reponse': {
            'field_name': 'audio_reponse',
            'input_name': f'question_{question.id}_audio',
            'label': 'Enregistrement audio',
            'accept': 'audio/*',
            'accept_mime': 'audio/webm,audio/mpeg,audio/wav,audio/ogg',
        },
        'video_reponse': {
            'field_name': 'video_reponse',
            'input_name': f'question_{question.id}_video',
            'label': 'Enregistrement vidéo',
            'accept': 'video/*',
            'accept_mime': 'video/webm,video/mp4',
        },
        'image_reponse': {
            'field_name': 'image_reponse',
            'input_name': f'question_{question.id}_image',
            'label': 'Télécharger une image',
            'accept': 'image/*',
            'accept_mime': 'image/png,image/jpeg,image/webp',
        },
        'fichier_reponse': {
            'field_name': 'fichier_reponse',
            'input_name': f'question_{question.id}_fichier',
            'label': 'Télécharger un fichier',
            'accept': '*/*',
            'accept_mime': '.pdf,.doc,.docx,.txt',
        },
    }
    return mapping.get(question.type_question, None)