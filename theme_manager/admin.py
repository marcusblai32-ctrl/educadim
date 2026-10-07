from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Theme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    """Administration du thème EducaDim, organisée par sections."""

    list_display = ('nom', 'site_name', 'actif', 'primary_color_preview', 'updated_at_display')
    list_filter = ('actif', 'maintenance_mode', 'evenement_actif')
    search_fields = ('nom', 'site_name', 'site_description')
    ordering = ('-actif', 'nom')
    list_per_page = 20

    fieldsets = (
        # ============================================================
        # INFORMATIONS GÉNÉRALES
        # ============================================================
        (_("Informations générales"), {
            'fields': (
                'nom',
                'site_name',
                'site_description',
                'actif',
            ),
            'classes': ('wide',),
        }),

        # ============================================================
        # LOGO & FAVICON
        # ============================================================
        (_("Logo & Favicon"), {
            'fields': (
                ('logo', 'logo_url'),
                ('favicon', 'favicon_url'),
            ),
        }),

        # ============================================================
        # SEO
        # ============================================================
        (_("SEO"), {
            'fields': (
                'meta_description',
                'meta_keywords',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # COULEURS PRINCIPALES
        # ============================================================
        (_("Couleurs principales"), {
            'fields': (
                ('primary', 'primary_hover'),
                ('secondary', 'secondary_hover'),
            ),
            'description': _("Choisissez les couleurs qui définissent l'identité visuelle de la plateforme."),
        }),

        # ============================================================
        # COULEURS D'ÉTAT
        # ============================================================
        (_("Couleurs d'état"), {
            'fields': (
                ('success', 'success_hover'),
                ('danger', 'danger_hover'),
                ('warning', 'warning_hover'),
                ('info', 'info_hover'),
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # FOND & TEXTE
        # ============================================================
        (_("Fond & Texte"), {
            'fields': (
                'body_bg',
                'text_color',
                'text_muted',
                ('white', 'light', 'dark'),
                'border',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # TYPOGRAPHIE & STYLE
        # ============================================================
        (_("Typographie & Style"), {
            'fields': (
                'font_family',
                'border_radius',
                'box_shadow',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # SECTION HERO
        # ============================================================
        (_("Section Hero — Contenu"), {
            'fields': (
                'hero_badge',
                'hero_title',
                'hero_subtitle_line2',
                'hero_subtitle',
                ('btn_explore', 'btn_start'),
            ),
        }),

        (_("Section Hero — Image / Stats"), {
            'fields': (
                ('hero_image', 'hero_image_url'),
                ('stats_cours', 'stats_etudiants', 'stats_satisfaction'),
            ),
        }),

        (_("Section Hero — Cartes"), {
            'fields': (
                ('hero_card1_title', 'hero_card1_icon'),
                'hero_card1_desc',
                ('hero_card2_title', 'hero_card2_icon'),
                'hero_card2_desc',
                ('hero_card3_title', 'hero_card3_icon'),
                'hero_card3_desc',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # SECTION FEATURES
        # ============================================================
        (_("Section Features — En-tête"), {
            'fields': (
                'features_tag',
                'features_title',
                'features_highlight',
                'feature_link_text',
            ),
            'classes': ('collapse',),
        }),

        (_("Section Features — Cartes"), {
            'fields': (
                ('feature1_title', 'feature1_icon', 'feature1_color'),
                'feature1_desc',
                ('feature2_title', 'feature2_icon', 'feature2_color'),
                'feature2_desc',
                ('feature3_title', 'feature3_icon', 'feature3_color'),
                'feature3_desc',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # SECTION CTA
        # ============================================================
        (_("Section CTA"), {
            'fields': (
                'cta_title',
                'cta_highlight',
                'cta_desc',
                'cta_btn',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # SECTION TÉMOIGNAGES
        # ============================================================
        (_("Section Témoignages — En-tête"), {
            'fields': (
                'testimonials_tag',
                'testimonials_title',
                'testimonials_highlight',
                'testimonials_end',
            ),
            'classes': ('collapse',),
        }),

        (_("Témoignage 1"), {
            'fields': (
                'testimonial1_text',
                ('testimonial1_name', 'testimonial1_job'),
                'testimonial1_avatar',
                'testimonial1_stars',
            ),
            'classes': ('collapse',),
        }),

        (_("Témoignage 2"), {
            'fields': (
                'testimonial2_text',
                ('testimonial2_name', 'testimonial2_job'),
                'testimonial2_avatar',
                'testimonial2_stars',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # PAGES STATIQUES
        # ============================================================
        (_("Page — À propos"), {
            'fields': (
                'about_title',
                'about_content',
                ('about_image', 'about_image_url'),
            ),
            'classes': ('collapse',),
        }),

        (_("Page — Contact"), {
            'fields': (
                'contact_page_title',
                'contact_page_subtitle',
                'contact_phone',
                'contact_address',
                'contact_hours',
                'contact_map_embed',
            ),
            'classes': ('collapse',),
        }),

        (_("Page — Conditions"), {
            'fields': ('conditions_title', 'conditions_content'),
            'classes': ('collapse',),
        }),

        (_("Page — Confidentialité"), {
            'fields': ('privacy_title', 'privacy_content'),
            'classes': ('collapse',),
        }),

        (_("Page — FAQ"), {
            'fields': ('faq_title', 'faq_content'),
            'classes': ('collapse',),
        }),

        # ============================================================
        # PIED DE PAGE
        # ============================================================
        (_("Pied de page"), {
            'fields': (
                'footer_text',
                'about_text',
                'contact_email',
            ),
        }),

        # ============================================================
        # ÉVÉNEMENT SPÉCIAL
        # ============================================================
        (_("Événement spécial"), {
            'fields': (
                'evenement_actif',
                ('evenement_banner', 'evenement_banner_url'),
                ('evenement_logo', 'evenement_logo_url'),
                'evenement_nom',
                'evenement_message',
                'evenement_hashtag',
            ),
            'classes': ('collapse',),
        }),

        # ============================================================
        # MAINTENANCE & WHATSAPP
        # ============================================================
        (_("Maintenance"), {
            'fields': (
                'maintenance_mode',
                'maintenance_message',
            ),
            'classes': ('collapse',),
        }),

        (_("WhatsApp"), {
            'fields': (
                'whatsapp_group',
                'whatsapp_contact',
            ),
            'classes': ('collapse',),
        }),
    )

    # ============================================================
    # COLONNES PERSONNALISÉES
    # ============================================================
    @admin.display(description=_("Couleur primaire"))
    def primary_color_preview(self, obj):
        """Affiche un aperçu de la couleur primaire."""
        if not obj.primary:
            return "—"
        return format_html(
            '<span style="display:inline-block; width:24px; height:24px; '
            'border-radius:50%; background:{}; border:1px solid #ccc; '
            'vertical-align:middle;"></span>'
            ' <code style="margin-left:6px;">{}</code>',
            obj.primary,
            obj.primary,
        )

    @admin.display(description=_("Dernière modification"))
    def updated_at_display(self, obj):
        """Affiche la dernière date de modification (si dispo)."""
        updated = getattr(obj, 'updated_at', None)
        if updated:
            return updated.strftime("%d/%m/%Y %H:%M")
        return "—"

    # ============================================================
    # ACTIONS PERSONNALISÉES
    # ============================================================
    actions = ['activer_theme', 'desactiver_theme']

    @admin.action(description=_("Activer les thèmes sélectionnés"))
    def activer_theme(self, request, queryset):
        queryset.update(actif=True)
        self.message_user(request, _("Thème(s) activé(s)."))

    @admin.action(description=_("Désactiver les thèmes sélectionnés"))
    def desactiver_theme(self, request, queryset):
        queryset.update(actif=False)
        self.message_user(request, _("Thème(s) désactivé(s)."))

    # ============================================================
    # SAUVEGARDE : garantir UN SEUL thème actif
    # ============================================================
    def save_model(self, request, obj, form, change):
        """Si le thème est actif, désactiver tous les autres."""
        super().save_model(request, obj, form, change)
        if obj.actif:
            Theme.objects.exclude(pk=obj.pk).update(actif=False)

    # ============================================================
    # PRÉVISUALISATION DES IMAGES
    # ============================================================
    readonly_fields = ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Afficher un aperçu des images uploadées."""
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name in ('logo', 'favicon', 'hero_image', 'about_image',
                              'testimonial1_avatar', 'testimonial2_avatar',
                              'evenement_banner', 'evenement_logo'):
            formfield.widget.attrs.update({
                'accept': 'image/*',
            })
        return formfield