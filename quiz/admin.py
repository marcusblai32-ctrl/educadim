from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Quiz, Question, Reponse, TentativeQuiz, ReponseUtilisateur


class ReponseInline(admin.TabularInline):
    model = Reponse
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True
    fieldsets = (
        (None, {'fields': ('type_question', 'texte', 'explication', 'points', 'ordre')}),
        ('Média de la question', {
            'fields': ('q_media_titre', 'q_media_audio_url', 'q_media_audio_file',
                       'q_media_video_url', 'q_media_video_file', 'q_media_image_url',
                       'q_media_image_file', 'q_media_texte'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('titre', 'get_niveau_display', 'pourcentage_reussite', 'duree_quiz', 'publie', 'created_at')
    list_filter = ('publie',)
    search_fields = ('titre', 'description', 'cours__titre', 'module__titre', 'lecon__titre')
    inlines = [QuestionInline]
    fieldsets = (
        (None, {'fields': ('titre', 'description', 'publie', 'pourcentage_reussite', 'duree_quiz')}),
        ('Relasyon', {'fields': ('cours', 'module', 'lecon'), 'description': 'Chwazi youn nan twa: Cours, Module, oswa Leçon.'}),
        ('Média du Quiz', {
            'fields': ('media_titre', 'media_audio_url', 'media_audio_file', 'media_video_url',
                       'media_video_file', 'media_image_url', 'media_image_file', 'media_texte'),
            'classes': ('collapse',)
        }),
    )

    def get_niveau_display(self, obj):
        niveau = obj.get_niveau()
        labels = {'cours': '📚 Cours', 'module': '📖 Module', 'lecon': '📝 Leçon', 'inconnu': '❓ Inconnu'}
        return labels.get(niveau, niveau)
    get_niveau_display.short_description = "Niveau"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'texte', 'type_question', 'points', 'ordre')
    list_filter = ('type_question',)
    search_fields = ('texte', 'quiz__titre')
    list_editable = ('points', 'ordre')
    inlines = [ReponseInline]
    fieldsets = (
        (None, {'fields': ('quiz', 'type_question', 'texte', 'explication', 'points', 'ordre')}),
        ('Média de la question', {
            'fields': ('q_media_titre', 'q_media_audio_url', 'q_media_audio_file',
                       'q_media_video_url', 'q_media_video_file', 'q_media_image_url',
                       'q_media_image_file', 'q_media_texte'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TentativeQuiz)
class TentativeQuizAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'quiz', 'score', 'reussi', 'date_debut', 'date_soumission', 'lien_correction')
    list_filter = ('reussi', 'quiz')
    search_fields = ('utilisateur__email', 'quiz__titre')
    readonly_fields = ('date_debut', 'date_soumission')

    def lien_correction(self, obj):
        if obj.date_soumission:
            url = reverse('quiz:corriger_tentative', args=[obj.id])
            return format_html(
                '<a class="button" href="{}" style="background:#28a745;color:white;padding:5px 10px;border-radius:4px;text-decoration:none;" target="_blank">✏️ Korije</a>',
                url
            )
        return "-"
    lien_correction.short_description = "Koreksyon"


@admin.register(ReponseUtilisateur)
class ReponseUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('tentative', 'question', 'get_fichye_type')
    search_fields = ('tentative__utilisateur__email', 'question__texte')
    readonly_fields = (
        'get_audio_player', 'get_video_player', 'get_image_preview', 'get_fichier_link',
    )
    fields = (
        'tentative', 'question', 'reponses_selectionnees', 'texte_reponse',
        'get_audio_player', 'get_video_player', 'get_image_preview', 'get_fichier_link',
        'audio_reponse', 'video_reponse', 'image_reponse', 'fichier_reponse',
        'points_attribues'
    )

    def get_fichye_type(self, obj):
        if obj.audio_reponse:
            return "🎵 Audio"
        if obj.video_reponse:
            return "🎬 Video"
        if obj.image_reponse:
            return "🖼️ Image"
        if obj.fichier_reponse:
            return "📎 Fichye"
        return "—"
    get_fichye_type.short_description = "Fichye"

    def get_audio_player(self, obj):
        if obj.audio_reponse:
            url = obj.audio_reponse.url
            return format_html(
                '<audio controls preload="metadata" style="width:400px;margin-top:5px;">'
                '<source src="{}" type="audio/webm; codecs=opus">'
                '<source src="{}" type="audio/webm">'
                '<source src="{}" type="audio/mpeg">'
                '<source src="{}" type="audio/mp4">'
                '<source src="{}" type="audio/ogg">'
                'Navigatè w pa sipòte audio.</audio><br>'
                '<a href="{}" target="_blank" style="margin-top:5px;display:inline-block;padding:4px 10px;background:#6c757d;color:#fff;border-radius:4px;text-decoration:none;">'
                '📥 Télécharger</a>',
                url, url, url, url, url, url
            )
        return "—"
    get_audio_player.short_description = "🎵 Lektè Audio"

    def get_video_player(self, obj):
        if obj.video_reponse:
            url = obj.video_reponse.url
            return format_html(
                '<video controls style="width:400px;margin-top:5px;">'
                '<source src="{}" type="video/webm">'
                '<source src="{}" type="video/mp4">'
                'Navigatè w pa sipòte video.</video><br>'
                '<a href="{}" target="_blank" style="margin-top:5px;display:inline-block;padding:4px 10px;background:#6c757d;color:#fff;border-radius:4px;text-decoration:none;">'
                '📥 Télécharger</a>',
                url, url, url
            )
        return "—"
    get_video_player.short_description = "🎬 Lektè Video"

    def get_image_preview(self, obj):
        if obj.image_reponse:
            return format_html(
                '<img src="{}" style="max-width:300px;max-height:300px;border-radius:6px;margin-top:5px;" /><br>'
                '<a href="{}" target="_blank" style="margin-top:5px;display:inline-block;padding:4px 10px;background:#6c757d;color:#fff;border-radius:4px;text-decoration:none;">'
                '📥 Télécharger</a>',
                obj.image_reponse.url, obj.image_reponse.url
            )
        return "—"
    get_image_preview.short_description = "🖼️ Apèsi Image"

    def get_fichier_link(self, obj):
        if obj.fichier_reponse:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="padding:4px 10px;background:#6c757d;color:#fff;border-radius:4px;text-decoration:none;">'
                '📥 Télécharger fichye</a>',
                obj.fichier_reponse.url
            )
        return "—"
    get_fichier_link.short_description = "📎 Lyen Fichye"