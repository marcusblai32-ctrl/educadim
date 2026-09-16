from django.urls import path
from . import views

app_name = 'quiz'

urlpatterns = [
    # ===== WOUT PIBLIK =====
    path('', views.quiz_list, name='list'),
    path('<int:pk>/', views.quiz_detail, name='detail'),
    path('<int:pk>/commencer/', views.start_quiz, name='start'),
    path('passer/<int:tentative_pk>/', views.take_quiz, name='take_quiz'),
    path('soumettre/<int:tentative_pk>/', views.submit_quiz, name='submit'),
    path('resultat/<int:tentative_pk>/', views.quiz_result, name='quiz_result'),
    path('question/<int:question_id>/upload-type/', views.get_question_upload_type, name='get_upload_type'),

    # ===== WOUT POU KOREKSYON STAFF =====
    path('correction/', views.tentative_list, name='tentative_list'),
    path('correction/<int:tentative_pk>/', views.corriger_tentative_view, name='corriger_tentative'),

    # ===== WOUT SEKIRIZE POU MEDIA (odyo, video, image, fichye) =====
    path('media/audio/<int:reponse_id>/', views.serve_audio_reponse, name='serve_audio'),
    path('media/video/<int:reponse_id>/', views.serve_video_reponse, name='serve_video'),
    path('media/image/<int:reponse_id>/', views.serve_image_reponse, name='serve_image'),
    path('media/fichier/<int:reponse_id>/', views.serve_fichier_reponse, name='serve_fichier'),
]