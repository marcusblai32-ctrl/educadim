import logging

from django.utils.translation import gettext as _

from .services import DEFAULT_SITE_NAME, css_version, get_active_theme, google_font_url, parse_color

logger = logging.getLogger(__name__)


def theme_processor(request):
    """Tèm aktif + done ki pare pou template yo (UN SÈL query pa requèt)."""
    try:
        theme = get_active_theme(request)
        return {
            "theme": theme,
            "maintenance_mode": bool(theme and theme.maintenance_mode),
            "maintenance_message": theme.maintenance_message if theme else "",
            # Done deja nèt pou template yo (pa bezwen if/else repete):
            "site_name": (theme.site_name if theme and theme.site_name else DEFAULT_SITE_NAME),
            "theme_css_version": css_version(theme),
            "theme_color": parse_color(theme.primary if theme else None, "#176b91"),
            "theme_font_url": google_font_url(theme.font_family) if theme else "",
        }
    except Exception:
        logger.exception("Error in theme_processor")
        return {
            "theme": None,
            "maintenance_mode": False,
            "maintenance_message": "",
            "site_name": DEFAULT_SITE_NAME,
            "theme_css_version": "0",
            "theme_color": "#176b91",
            "theme_font_url": "",
        }


def breadcrumbs_processor(request):
    """Kreye breadcrumbs pou navigasyon an"""
    path = request.path
    parts = path.strip('/').split('/')
    breadcrumbs = []
    current_path = ''

    # Sote prefiks lang (fr/, ht/)
    start_idx = 0
    if parts and parts[0] in ['fr', 'ht']:
        start_idx = 1

    names = {
        'cours': _('Cours'),
        'inscriptions': _('Inscriptions'),
        'progression': _('Progression'),
        'quiz': _('Quiz'),
        'presence': _('Présences'),
        'badges': _('Badges'),
        'classement': _('Classement'),
        'chat': _('Chat'),
        'notifications': _('Notifications'),
        'contact': _('Contact'),
        'a-propos': _('À propos'),
        'conditions': _('Conditions'),
        'confidentialite': _('Confidentialité'),
        'faq': _('FAQ'),
        'dashboard': _('Tableau de bord'),
        'todo': _('Todo'),
        'theme': _('Thème'),
        'ads': _('Annonces'),
        'connexion': _('Connexion'),
        'inscription': _('Inscription'),
        'profil': _('Profil'),
        'supprimer': _('Supprimer'),
        'mot-de-passe-oublie': _('Mot de passe oublié'),
        'reinitialiser': _('Réinitialiser'),
        'modifier': _('Modifier'),
        'ajouter': _('Ajouter'),
        'liste': _('Liste'),
        'detail': _('Détail'),
    }

    for part in parts[start_idx:]:
        if part:
            current_path += '/' + part
            name = names.get(part, part.replace('-', ' ').replace('_', ' ').title())
            breadcrumbs.append({'name': name, 'url': current_path})

    return {'breadcrumbs': breadcrumbs}


def seo_processor(request):
    """Meta description/keywords pou SEO (itilize menm tèm memoize a, pa gen query ankò)."""
    try:
        theme = get_active_theme(request)
        return {
            "meta_description": (theme.meta_description or theme.site_description) if theme else "",
            "meta_keywords": theme.meta_keywords if theme else "",
        }
    except Exception:
        return {"meta_description": "", "meta_keywords": ""}
