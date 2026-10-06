from django.db import models
from django.utils.translation import gettext_lazy as _


class Theme(models.Model):
    # ===== INFORMATIONS GENERALES =====
    nom = models.CharField(max_length=100, default="Défaut", verbose_name="Nom du thème")
    site_name = models.CharField(max_length=100, default="EducDim", verbose_name="Nom du site")
    site_description = models.TextField(blank=True, verbose_name="Description du site")
    actif = models.BooleanField(default=True, verbose_name="Actif")

    # ===== LOGO & FAVICON =====
    logo = models.ImageField(upload_to='theme/logos/', blank=True, null=True, verbose_name="Logo")
    logo_url = models.URLField(blank=True, verbose_name="URL du logo")
    favicon = models.ImageField(upload_to='theme/favicons/', blank=True, null=True, verbose_name="Favicon")
    favicon_url = models.URLField(blank=True, verbose_name="URL du favicon")

    # ===== SEO =====
    meta_description = models.CharField(max_length=255, blank=True, verbose_name="Meta description")
    meta_keywords = models.CharField(max_length=255, blank=True, verbose_name="Meta keywords")

    # ===== COULEURS PRINCIPALES =====
    primary = models.CharField(max_length=7, default="#1a1a2e", verbose_name="Primaire")
    primary_hover = models.CharField(max_length=7, default="#2d2d4a", verbose_name="Primaire (hover)")
    secondary = models.CharField(max_length=7, default="#16213e", verbose_name="Secondaire")
    secondary_hover = models.CharField(max_length=7, default="#2a3a6a", verbose_name="Secondaire (hover)")

    # ===== COULEURS D'ETAT =====
    success = models.CharField(max_length=7, default="#28a745", verbose_name="Succès")
    success_hover = models.CharField(max_length=7, default="#218838", verbose_name="Succès (hover)")
    danger = models.CharField(max_length=7, default="#dc3545", verbose_name="Danger")
    danger_hover = models.CharField(max_length=7, default="#c82333", verbose_name="Danger (hover)")
    warning = models.CharField(max_length=7, default="#ffc107", verbose_name="Avertissement")
    warning_hover = models.CharField(max_length=7, default="#e0a800", verbose_name="Avertissement (hover)")
    info = models.CharField(max_length=7, default="#17a2b8", verbose_name="Information")
    info_hover = models.CharField(max_length=7, default="#138496", verbose_name="Information (hover)")

    # ===== FOND ET TEXTE =====
    body_bg = models.CharField(max_length=7, default="#f8f9fa", verbose_name="Fond de page")
    text_color = models.CharField(max_length=7, default="#212529", verbose_name="Couleur du texte")
    text_muted = models.CharField(max_length=7, default="#6c757d", verbose_name="Texte secondaire")
    white = models.CharField(max_length=7, default="#ffffff", verbose_name="Blanc")
    light = models.CharField(max_length=7, default="#f8f9fa", verbose_name="Clair")
    dark = models.CharField(max_length=7, default="#1a1a2e", verbose_name="Foncé")
    border = models.CharField(max_length=7, default="#dee2e6", verbose_name="Bordure")

    # ===== TYPOGRAPHIE ET STYLE =====
    font_family = models.CharField(
        max_length=200,
        default="'Inter', sans-serif",
        verbose_name="Police de caractères"
    )
    border_radius = models.CharField(
        max_length=10,
        default="8px",
        verbose_name="Rayon des bordures"
    )
    box_shadow = models.CharField(
        max_length=100,
        default="0 4px 20px rgba(0,0,0,0.08)",
        verbose_name="Ombre des cartes"
    )

    # ===== SECTION HERO =====
    hero_title = models.CharField(max_length=200, blank=True, verbose_name="Titre du Hero")
    hero_subtitle = models.CharField(max_length=200, blank=True, verbose_name="Sous-titre du Hero")
    hero_badge = models.CharField(max_length=100, blank=True, verbose_name="Badge")
    hero_subtitle_line2 = models.CharField(max_length=200, blank=True, verbose_name="Sous-titre (ligne 2)")

    btn_explore = models.CharField(max_length=50, blank=True, verbose_name="Bouton Explorer")
    btn_start = models.CharField(max_length=50, blank=True, verbose_name="Bouton Commencer")

    hero_image = models.ImageField(upload_to='theme/hero/', blank=True, null=True, verbose_name="Image du Hero")
    hero_image_url = models.URLField(blank=True, verbose_name="URL image du Hero")

    stats_etudiants = models.CharField(max_length=50, blank=True, verbose_name="Stats - Étudiants")
    stats_cours = models.CharField(max_length=50, blank=True, verbose_name="Stats - Cours")
    stats_satisfaction = models.CharField(max_length=50, blank=True, verbose_name="Stats - Satisfaction")

    # ===== HERO - CARTES =====
    hero_card1_title = models.CharField(max_length=100, blank=True, verbose_name="Carte 1 - Titre")
    hero_card1_desc = models.TextField(blank=True, verbose_name="Carte 1 - Description")
    hero_card1_icon = models.CharField(max_length=50, blank=True, verbose_name="Carte 1 - Icône")

    hero_card2_title = models.CharField(max_length=100, blank=True, verbose_name="Carte 2 - Titre")
    hero_card2_desc = models.TextField(blank=True, verbose_name="Carte 2 - Description")
    hero_card2_icon = models.CharField(max_length=50, blank=True, verbose_name="Carte 2 - Icône")

    hero_card3_title = models.CharField(max_length=100, blank=True, verbose_name="Carte 3 - Titre")
    hero_card3_desc = models.TextField(blank=True, verbose_name="Carte 3 - Description")
    hero_card3_icon = models.CharField(max_length=50, blank=True, verbose_name="Carte 3 - Icône")

    # ===== SECTION FEATURES =====
    features_tag = models.CharField(max_length=50, blank=True, verbose_name="Tag Features")
    features_title = models.CharField(max_length=200, blank=True, verbose_name="Titre Features")
    features_highlight = models.CharField(max_length=50, blank=True, verbose_name="Mot en surbrillance")

    feature1_title = models.CharField(max_length=100, blank=True, verbose_name="Feature 1 - Titre")
    feature1_desc = models.TextField(blank=True, verbose_name="Feature 1 - Description")
    feature1_icon = models.CharField(max_length=50, blank=True, verbose_name="Feature 1 - Icône")
    feature1_color = models.CharField(max_length=7, blank=True, verbose_name="Feature 1 - Couleur")

    feature2_title = models.CharField(max_length=100, blank=True, verbose_name="Feature 2 - Titre")
    feature2_desc = models.TextField(blank=True, verbose_name="Feature 2 - Description")
    feature2_icon = models.CharField(max_length=50, blank=True, verbose_name="Feature 2 - Icône")
    feature2_color = models.CharField(max_length=7, blank=True, verbose_name="Feature 2 - Couleur")

    feature3_title = models.CharField(max_length=100, blank=True, verbose_name="Feature 3 - Titre")
    feature3_desc = models.TextField(blank=True, verbose_name="Feature 3 - Description")
    feature3_icon = models.CharField(max_length=50, blank=True, verbose_name="Feature 3 - Icône")
    feature3_color = models.CharField(max_length=7, blank=True, verbose_name="Feature 3 - Couleur")

    feature_link_text = models.CharField(max_length=50, blank=True, verbose_name="Texte du lien")

    # ===== SECTION CTA =====
    cta_title = models.CharField(max_length=200, blank=True, verbose_name="CTA - Titre")
    cta_highlight = models.CharField(max_length=50, blank=True, verbose_name="CTA - Mot en surbrillance")
    cta_desc = models.TextField(blank=True, verbose_name="CTA - Description")
    cta_btn = models.CharField(max_length=50, blank=True, verbose_name="CTA - Bouton")

    # ===== SECTION TEMOIGNAGES =====
    testimonials_tag = models.CharField(max_length=50, blank=True, verbose_name="Tag Témoignages")
    testimonials_title = models.CharField(max_length=200, blank=True, verbose_name="Titre Témoignages")
    testimonials_highlight = models.CharField(max_length=50, blank=True, verbose_name="Mot en surbrillance")
    testimonials_end = models.CharField(max_length=200, blank=True, verbose_name="Fin du titre")

    testimonial1_text = models.TextField(blank=True, verbose_name="Témoignage 1 - Texte")
    testimonial1_name = models.CharField(max_length=100, blank=True, verbose_name="Témoignage 1 - Nom")
    testimonial1_job = models.CharField(max_length=100, blank=True, verbose_name="Témoignage 1 - Poste")
    testimonial1_avatar = models.ImageField(upload_to='theme/testimonials/', blank=True, null=True, verbose_name="Témoignage 1 - Avatar")
    testimonial1_stars = models.IntegerField(default=5, verbose_name="Témoignage 1 - Étoiles")

    testimonial2_text = models.TextField(blank=True, verbose_name="Témoignage 2 - Texte")
    testimonial2_name = models.CharField(max_length=100, blank=True, verbose_name="Témoignage 2 - Nom")
    testimonial2_job = models.CharField(max_length=100, blank=True, verbose_name="Témoignage 2 - Poste")
    testimonial2_avatar = models.ImageField(upload_to='theme/testimonials/', blank=True, null=True, verbose_name="Témoignage 2 - Avatar")
    testimonial2_stars = models.IntegerField(default=5, verbose_name="Témoignage 2 - Étoiles")

    # ===== PAGE - A PROPOS =====
    about_title = models.CharField(max_length=200, blank=True, verbose_name="Titre - À propos")
    about_content = models.TextField(blank=True, verbose_name="Contenu - À propos")
    about_image = models.ImageField(upload_to='theme/about/', blank=True, null=True, verbose_name="Image - À propos")
    about_image_url = models.URLField(blank=True, verbose_name="URL image - À propos")

    # ===== PAGE - CONTACT =====
    contact_page_title = models.CharField(max_length=200, blank=True, verbose_name="Titre - Contact")
    contact_page_subtitle = models.CharField(max_length=200, blank=True, verbose_name="Sous-titre - Contact")
    contact_phone = models.CharField(max_length=50, blank=True, verbose_name="Téléphone")
    contact_address = models.TextField(blank=True, verbose_name="Adresse")
    contact_hours = models.CharField(max_length=200, blank=True, verbose_name="Heures d'ouverture")
    contact_map_embed = models.TextField(blank=True, verbose_name="Carte Google Maps")

    # ===== PAGE - CONDITIONS =====
    conditions_title = models.CharField(max_length=200, blank=True, verbose_name="Titre - Conditions")
    conditions_content = models.TextField(blank=True, verbose_name="Contenu - Conditions")

    # ===== PAGE - CONFIDENTIALITE =====
    privacy_title = models.CharField(max_length=200, blank=True, verbose_name="Titre - Confidentialité")
    privacy_content = models.TextField(blank=True, verbose_name="Contenu - Confidentialité")

    # ===== PAGE - FAQ =====
    faq_title = models.CharField(max_length=200, blank=True, verbose_name="Titre - FAQ")
    faq_content = models.TextField(blank=True, verbose_name="Contenu - FAQ")

    # ===== PIED DE PAGE =====
    footer_text = models.CharField(max_length=255, blank=True, verbose_name="Texte du pied de page")
    about_text = models.TextField(blank=True, verbose_name="À propos (pied de page)")
    contact_email = models.EmailField(blank=True, verbose_name="Email de contact")

    # ===== EVENEMENT SPECIAL =====
    evenement_actif = models.BooleanField(default=False, verbose_name="Événement actif")
    evenement_banner = models.ImageField(upload_to='theme/evenements/', blank=True, null=True, verbose_name="Bannière")
    evenement_banner_url = models.URLField(blank=True, verbose_name="URL bannière")
    evenement_nom = models.CharField(max_length=200, blank=True, verbose_name="Nom de l'événement")
    evenement_logo = models.ImageField(upload_to='theme/evenements/', blank=True, null=True, verbose_name="Logo de l'événement")
    evenement_logo_url = models.URLField(blank=True, verbose_name="URL logo")
    evenement_message = models.TextField(blank=True, verbose_name="Message")
    evenement_hashtag = models.CharField(max_length=50, blank=True, verbose_name="Hashtag")

    # ===== MAINTENANCE & WHATSAPP =====
    maintenance_mode = models.BooleanField(default=False, verbose_name="Mode maintenance")
    maintenance_message = models.TextField(blank=True, verbose_name="Message de maintenance")
    whatsapp_group = models.URLField(blank=True, verbose_name="Lien groupe WhatsApp")
    whatsapp_contact = models.URLField(blank=True, verbose_name="Lien contact WhatsApp")

    class Meta:
        verbose_name = _("Thème")
        verbose_name_plural = _("Thèmes")
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({'Actif' if self.actif else 'Inactif'})"

    # ===== METHODES POU IMAJ =====
    @staticmethod
    def _file_url(field):
        """
        URL yon ImageField. Si admin te mete yon URL konplè nan chan fichye a
        (egzanp https://ui-avatars.com/...), non fichye a SE URL la : li dwe sèvi dirèkteman.
        Rele .url sou li ta bay yon lyen kase (domèn stockage + URL la).
        """
        if not field or not getattr(field, "name", ""):
            return None
        name = field.name
        if name.startswith(("https://", "http://")):
            return name
        try:
            return field.url
        except Exception:
            return None

    def get_logo(self):
        return self._file_url(self.logo) or self.logo_url or None

    def get_favicon(self):
        return self._file_url(self.favicon) or self.favicon_url or None

    def get_hero_image(self):
        return self._file_url(self.hero_image) or self.hero_image_url or None

    def get_about_image(self):
        return self._file_url(self.about_image) or self.about_image_url or None

    def get_evenement_banner(self):
        return self._file_url(self.evenement_banner) or self.evenement_banner_url or None

    def get_evenement_logo(self):
        return self._file_url(self.evenement_logo) or self.evenement_logo_url or None

    def get_testimonial1_avatar(self):
        return self._file_url(self.testimonial1_avatar)

    def get_testimonial2_avatar(self):
        return self._file_url(self.testimonial2_avatar)