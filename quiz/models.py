from django.db import models
from django.conf import settings
from django.utils import timezone


class Quiz(models.Model):
    cours = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='quiz', null=True, blank=True, verbose_name="Cours")
    module = models.ForeignKey('courses.Module', on_delete=models.CASCADE, related_name='quiz', null=True, blank=True, verbose_name="Module")
    lecon = models.ForeignKey('courses.Lecon', on_delete=models.CASCADE, related_name='quiz', null=True, blank=True, verbose_name="Leçon")

    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    publie = models.BooleanField(default=False)
    pourcentage_reussite = models.PositiveIntegerField(default=70)
    duree_quiz = models.PositiveIntegerField(default=15, verbose_name="Durée du quiz (minutes)", help_text="Temps limite pour compléter le quiz en minutes.")
    created_at = models.DateTimeField(auto_now_add=True)

    media_audio_url = models.URLField(blank=True, verbose_name="URL Audio")
    media_audio_file = models.FileField(upload_to='quiz/media/audio/', blank=True, null=True, verbose_name="Fichier Audio")
    media_video_url = models.URLField(blank=True, verbose_name="URL Vidéo")
    media_video_file = models.FileField(upload_to='quiz/media/video/', blank=True, null=True, verbose_name="Fichier Vidéo")
    media_image_url = models.URLField(blank=True, verbose_name="URL Image")
    media_image_file = models.ImageField(upload_to='quiz/media/images/', blank=True, null=True, verbose_name="Fichier Image")
    media_texte = models.TextField(blank=True, verbose_name="Texte du média")
    media_titre = models.CharField(max_length=200, blank=True, verbose_name="Titre du média")

    class Meta:
        verbose_name = "Quiz"
        verbose_name_plural = "Quiz"
        ordering = ['-created_at']

    def __str__(self):
        if self.cours:
            return f"[Cours] {self.titre}"
        elif self.module:
            return f"[Module] {self.titre}"
        elif self.lecon:
            return f"[Leçon] {self.titre}"
        return self.titre

    def has_media(self):
        return any([self.media_audio_url, self.media_audio_file, self.media_video_url, self.media_video_file, self.media_image_url, self.media_image_file, self.media_texte])

    def get_cours_parent(self):
        if self.cours:
            return self.cours
        elif self.module:
            return self.module.unite.cours
        elif self.lecon:
            return self.lecon.module.unite.cours
        return None

    def get_niveau(self):
        if self.cours:
            return "cours"
        elif self.module:
            return "module"
        elif self.lecon:
            return "lecon"
        return "inconnu"

    def get_duree_seconds(self):
        return self.duree_quiz * 60


class Question(models.Model):
    TYPES_QUESTION = [
        ('single', 'Choix unique'),
        ('multiple', 'Choix multiples'),
        ('vrai_faux', 'Vrai/Faux'),
        ('texte_trous', 'Texte à trous'),
        ('audio_comprehension', 'Compréhension audio'),
        ('video_comprehension', 'Compréhension vidéo'),
        ('audio_reponse', 'Réponse audio (enregistrement)'),
        ('video_reponse', 'Réponse vidéo (enregistrement)'),
        ('image_reponse', 'Réponse image (téléchargement)'),
        ('fichier_reponse', 'Réponse fichier (téléchargement)'),
        ('texte_libre', 'Réponse texte libre'),
    ]
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    type_question = models.CharField(max_length=25, choices=TYPES_QUESTION)
    texte = models.TextField()
    explication = models.TextField(blank=True)
    points = models.PositiveIntegerField(default=1)
    ordre = models.PositiveIntegerField(default=1)

    q_media_audio_url = models.URLField(blank=True, verbose_name="URL Audio")
    q_media_audio_file = models.FileField(upload_to='quiz/questions/audio/', blank=True, null=True, verbose_name="Fichier Audio")
    q_media_video_url = models.URLField(blank=True, verbose_name="URL Vidéo")
    q_media_video_file = models.FileField(upload_to='quiz/questions/video/', blank=True, null=True, verbose_name="Fichier Vidéo")
    q_media_image_url = models.URLField(blank=True, verbose_name="URL Image")
    q_media_image_file = models.ImageField(upload_to='quiz/questions/images/', blank=True, null=True, verbose_name="Fichier Image")
    q_media_texte = models.TextField(blank=True, verbose_name="Texte du média")
    q_media_titre = models.CharField(max_length=200, blank=True, verbose_name="Titre du média")

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['quiz', 'ordre']

    def __str__(self):
        return f"{self.quiz.titre} - Q{self.ordre}: {self.texte[:50]}"

    def has_media(self):
        return any([self.q_media_audio_url, self.q_media_audio_file, self.q_media_video_url, self.q_media_video_file, self.q_media_image_url, self.q_media_image_file, self.q_media_texte])

    def is_upload_type(self):
        return self.type_question in ['audio_reponse', 'video_reponse', 'image_reponse', 'fichier_reponse']


class Reponse(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='reponses')
    texte = models.CharField(max_length=500)
    est_correcte = models.BooleanField(default=False)
    ordre = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Réponse"
        verbose_name_plural = "Réponses"
        ordering = ['question', 'ordre']

    def __str__(self):
        return f"{self.question.texte[:30]} -> {self.texte}"


class TentativeQuiz(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tentatives_quiz')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='tentatives')
    date_debut = models.DateTimeField(auto_now_add=True)
    date_soumission = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    reussi = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Tentative de quiz"
        verbose_name_plural = "Tentatives de quiz"

    def __str__(self):
        return f"{self.utilisateur.get_full_name()} - {self.quiz.titre} ({self.score}%)"


class ReponseUtilisateur(models.Model):
    tentative = models.ForeignKey(TentativeQuiz, on_delete=models.CASCADE, related_name='reponses_utilisateur')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    reponses_selectionnees = models.ManyToManyField(Reponse, blank=True)
    texte_reponse = models.TextField(blank=True)

    audio_reponse = models.FileField(upload_to='quiz/reponses/audio/', blank=True, null=True, verbose_name="Réponse audio")
    video_reponse = models.FileField(upload_to='quiz/reponses/video/', blank=True, null=True, verbose_name="Réponse vidéo")
    image_reponse = models.ImageField(upload_to='quiz/reponses/images/', blank=True, null=True, verbose_name="Réponse image")
    fichier_reponse = models.FileField(upload_to='quiz/reponses/fichiers/', blank=True, null=True, verbose_name="Réponse fichier")

    points_attribues = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="Points attribués (manuel)")

    class Meta:
        unique_together = ('tentative', 'question')
        verbose_name = "Réponse de l'utilisateur"
        verbose_name_plural = "Réponses des utilisateurs"

    def __str__(self):
        return f"{self.tentative.utilisateur.get_full_name()} - {self.question.texte[:30]}"

    def has_uploaded_file(self):
        return any([self.audio_reponse, self.video_reponse, self.image_reponse, self.fichier_reponse])

    def get_uploaded_file_url(self):
        t = self.question.type_question
        if t == 'audio_reponse' and self.audio_reponse:
            return self.audio_reponse.url
        elif t == 'video_reponse' and self.video_reponse:
            return self.video_reponse.url
        elif t == 'image_reponse' and self.image_reponse:
            return self.image_reponse.url
        elif t == 'fichier_reponse' and self.fichier_reponse:
            return self.fichier_reponse.url
        return None