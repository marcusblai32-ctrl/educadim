from django.contrib import admin
from .models import (
    Course, Unite, Module, Lecon, SectionLecon, Contenu,
    Category, Niveau, Promotions, LearningPath, CoursePrerequisite
)


class UniteInline(admin.TabularInline):
    model = Unite
    extra = 0
    show_change_link = True


class ModuleInline(admin.TabularInline):
    model = Module
    extra = 0
    show_change_link = True


class LeconInline(admin.TabularInline):
    model = Lecon
    extra = 0
    show_change_link = True


class SectionInline(admin.TabularInline):
    model = SectionLecon
    extra = 0
    show_change_link = True


class ContenuInline(admin.TabularInline):
    model = Contenu
    extra = 0
    fields = ('type_contenu', 'titre', 'titre_ht', 'ordre')
    show_change_link = True


# ============================================
# LEARNING PATH ADMIN
# ============================================
@admin.register(LearningPath)
class LearningPathAdmin(admin.ModelAdmin):
    list_display = ('nom', 'actif', 'created_at')
    search_fields = ('nom', 'description')
    list_filter = ('actif',)


# ============================================
# COURSE PREREQUISITE ADMIN
# ============================================
@admin.register(CoursePrerequisite)
class CoursePrerequisiteAdmin(admin.ModelAdmin):
    list_display = ('cours', 'prerequis', 'obligatoire')
    search_fields = ('cours__titre', 'prerequis__titre')
    list_filter = ('obligatoire',)


# ============================================
# CATEGORY ADMIN
# ============================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('nom', 'actif', 'ordre')
    search_fields = ('nom',)
    list_filter = ('actif',)


# ============================================
# NIVEAU ADMIN — KORIJE: Ajoute search_fields
# ============================================
@admin.register(Niveau)
class NiveauAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)  # ← SA A TE MANKE


# ============================================
# PROMOTIONS ADMIN
# ============================================
@admin.register(Promotions)
class PromotionsAdmin(admin.ModelAdmin):
    list_display = ('nom', 'nivo', 'date_debut', 'date_fin', 'actif')
    filter_horizontal = ('etudiants',)
    search_fields = ('nom',)
    list_filter = ('actif', 'nivo')


# ============================================
# COURSE ADMIN
# ============================================
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('titre', 'prix', 'publie', 'categorie', 'nivo', 'learning_path', 'position', 'created_at')
    list_filter = ('publie', 'categorie', 'nivo', 'inscription_ouverte', 'learning_path')
    search_fields = ('titre', 'description')
    inlines = [UniteInline]
    autocomplete_fields = ('categorie', 'nivo', 'learning_path')
    fieldsets = (
        ('Informations générales', {
            'fields': ('titre', 'description', 'image_url', 'image', 'prix', 'publie', 'created_by')
        }),
        ('Version créole', {
            'fields': ('titre_ht', 'description_ht'),
        }),
        ('Catégorisation', {
            'fields': ('categorie', 'nivo', 'duree')
        }),
        ('Learning Path', {
            'fields': ('learning_path', 'position'),
            'classes': ('collapse',)
        }),
        ('Inscriptions', {
            'fields': ('inscription_ouverte', 'date_debut_inscription', 'date_fin_inscription', 'promotion')
        }),
    )
    readonly_fields = ('created_by',)
    
    def save_model(self, request, obj, form, change):
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


# ============================================
# UNITE ADMIN
# ============================================
@admin.register(Unite)
class UniteAdmin(admin.ModelAdmin):
    list_display = ('titre', 'cours', 'ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre', 'cours__titre')
    inlines = [ModuleInline]


# ============================================
# MODULE ADMIN
# ============================================
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('titre', 'unite', 'ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre', 'unite__titre')
    inlines = [LeconInline]


# ============================================
# LECON ADMIN
# ============================================
@admin.register(Lecon)
class LeconAdmin(admin.ModelAdmin):
    list_display = ('titre', 'module', 'ordre', 'actif')
    list_filter = ('actif',)
    search_fields = ('titre', 'module__titre')
    inlines = [SectionInline]
    fieldsets = (
        ('Version française', {'fields': ('module', 'titre', 'description', 'contenu', 'ordre', 'actif')}),
        ('Version créole', {'fields': ('titre_ht', 'description_ht')}),
    )


# ============================================
# SECTION LECON ADMIN
# ============================================
@admin.register(SectionLecon)
class SectionLeconAdmin(admin.ModelAdmin):
    list_display = ('titre', 'lecon', 'type_section', 'ordre')
    list_filter = ('type_section',)
    search_fields = ('titre', 'lecon__titre')
    inlines = [ContenuInline]


# ============================================
# CONTENU ADMIN
# ============================================
@admin.register(Contenu)
class ContenuAdmin(admin.ModelAdmin):
    list_display = ('titre', 'section', 'type_contenu', 'ordre')
    list_filter = ('type_contenu',)
    search_fields = ('titre', 'section__titre')
    fieldsets = (
        (None, {'fields': ('section', 'type_contenu', 'ordre')}),
        ('Version Française', {
            'fields': ('titre', 'texte', 'url_video', 'url_image', 'url_audio', 'url_pdf', 'url_lien')
        }),
        ('Version Créole', {
            'fields': ('titre_ht', 'texte_ht', 'url_video_ht', 'url_image_ht', 'url_audio_ht', 'url_pdf_ht', 'url_lien_ht')
        }),
        ('Fichiers locaux (optionnel)', {
            'fields': ('fichier_audio', 'image', 'fichier_pdf', 'fichier'),
            'classes': ('collapse',)
        }),
    )