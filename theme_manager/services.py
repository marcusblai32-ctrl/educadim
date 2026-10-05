"""
Sèl kote kote tèm aktif la chaje ak CSS dinamik la jenere.

- get_active_theme(request): UN SÈL query pa requèt (context processors, middleware ak
  views pataje menm rezilta a).
- build_css(theme): CSS variables ki gen sekirite (valè envalid yo sote, yo pa janm
  anjeksyone nan CSS) + nuans (light/dark/darker) kalkile otomatikman.
"""
import hashlib
import logging
import re

from django.db import DatabaseError

from .models import Theme

logger = logging.getLogger(__name__)

_MISSING = object()

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
LENGTH_RE = re.compile(r"^\d{1,3}(?:\.\d{1,2})?(?:px|rem|em)$")
FONT_RE = re.compile(r"^[\w\s,'\"\-\.]{1,200}$")
SHADOW_RE = re.compile(r"^[\w\s,\.\-\(\)#%]{1,200}$")

DEFAULT_SITE_NAME = "EducaDim"


# ------------------------------------------------------------------ THEME LOADING
def get_active_theme(request=None):
    """Tèm aktif la (oswa None). Memoize sou request la pou evite query repete."""
    if request is not None:
        cached = getattr(request, "_active_theme", _MISSING)
        if cached is not _MISSING:
            return cached
    try:
        theme = Theme.objects.filter(actif=True).order_by("nom", "pk").first()
        if theme is None and not Theme.objects.exists():
            # Premye deplwaye: kreye yon tèm default sèlman si pa gen OKENN tèm
            theme = Theme.objects.create(actif=True, nom="Défaut", site_name=DEFAULT_SITE_NAME)
    except DatabaseError:
        logger.exception("Unable to load active theme")
        theme = None
    except Exception:
        logger.exception("Unexpected error loading active theme")
        theme = None
    if request is not None:
        request._active_theme = theme
    return theme


# ------------------------------------------------------------------ COLOR HELPERS
def safe_color(value, default=None):
    """Retounen koulè a si se yon hex valid (#rgb/#rrggbb), sinon default."""
    value = (value or "").strip()
    return value if HEX_RE.match(value) else default


def _to_rgb(color):
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in rgb)


def mix(color, other, amount):
    """Melanje `color` ak `other` (amount 0..1)."""
    a, b = _to_rgb(color), _to_rgb(other)
    return _to_hex([a[i] + (b[i] - a[i]) * amount for i in range(3)])


def lighten(color, amount):
    return mix(color, "#ffffff", amount)


def darken(color, amount):
    return mix(color, "#000000", amount)


def rgb_triplet(color):
    return "%d, %d, %d" % _to_rgb(color)


def _luminance(color):
    def channel(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in _to_rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def on_color(color):
    """Koulè tèks ki lizib sou `color` (blan oswa prèske nwa)."""
    return "#ffffff" if _luminance(color) < 0.5 else "#111827"


# ------------------------------------------------------------------ CSS BUILDING
_BRAND = [
    # (non variab, chan modèl, default)
    ("primary", "primary", "#176b91"),
    ("secondary", "secondary", "#45b7c7"),
    ("success", "success", "#257b63"),
    ("danger", "danger", "#dc3545"),
    ("warning", "warning", "#f59e0b"),
    ("info", "info", "#38bdf8"),
]

GENERIC_FONTS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-sans-serif",
    "ui-serif", "ui-monospace", "-apple-system", "blinkmacsystemfont", "segoe ui", "roboto",
    "helvetica", "helvetica neue", "arial", "tahoma", "verdana", "georgia", "times new roman",
}
_FONT_NAME_RE = re.compile(r"^[A-Za-z0-9 ]{2,40}$")


def google_font_url(font_family):
    """
    URL Google Fonts pou premye fanmi nan `font_family` (egzanp "'Inter', sans-serif").
    Retounen "" si se yon font sistèm oswa si non an pa sou.
    Se sa ki fè font admin chwazi a CHAJE pou tout bon (anvan, li te rete 'Inter' san chaje).
    """
    first = (font_family or "").split(",")[0].strip().strip("'\"")
    if not _FONT_NAME_RE.match(first) or first.lower() in GENERIC_FONTS:
        return ""
    family = first.replace(" ", "+")
    return f"https://fonts.googleapis.com/css2?family={family}:wght@400;500;600;700;800&display=swap"


def _brand_vars(theme, dark=False):
    """Koulè mak yo + vèsyon Bootstrap (--bs-*). dark=True bay nuans ki lizib sou fon fonse."""
    lines = []
    for name, field, default in _BRAND:
        base = safe_color(getattr(theme, field, None), default)
        hover = safe_color(getattr(theme, f"{field}_hover", None), darken(base, 0.1))
        if dark:
            # Sou fon fonse a, koulè a dwe pi klè pou rete lizib
            base = lighten(base, 0.25)
            hover = lighten(base, 0.12)
        lines += [
            f"--{name}: {base};",
            f"--{name}-hover: {hover};",
            f"--{name}-light: {lighten(base, 0.3)};",
            f"--{name}-lighter: {lighten(base, 0.65)};",
            f"--{name}-dark: {darken(base, 0.18)};",
            f"--{name}-darker: {darken(base, 0.38)};",
            f"--{name}-rgb: {rgb_triplet(base)};",
            f"--on-{name}: {on_color(base)};",
            # ----- Bootstrap suiv menm koulè a -----
            f"--bs-{name}: {base};",
            f"--bs-{name}-rgb: {rgb_triplet(base)};",
        ]
        if name == "primary":
            lines += [
                f"--bs-link-color: {base};",
                f"--bs-link-color-rgb: {rgb_triplet(base)};",
                f"--bs-link-hover-color: {hover};",
                f"--bs-link-hover-color-rgb: {rgb_triplet(hover)};",
            ]
    secondary = safe_color(getattr(theme, "secondary", None), "#45b7c7")
    primary = safe_color(getattr(theme, "primary", None), "#176b91")
    if dark:
        primary, secondary = lighten(primary, 0.25), lighten(secondary, 0.25)
    lines.append(f"--grad-brand: linear-gradient(120deg, {primary}, {secondary});")
    return lines


def _surface_vars(theme):
    """
    Siperfis (fon, kat, tèks, bordi). SE NON VARIAB SIT LA ITILIZE VRÈMAN
    (--bg, --bg-card, --glass-*...), pa sèlman --bg-body. Sa se kòz prensipal
    poukisa tèm lan pa t parèt anvan.
    """
    c = {f: safe_color(getattr(theme, f, None)) for f in
         ("body_bg", "text_color", "text_muted", "white", "light", "dark", "border")}
    lines = []
    if c["body_bg"]:
        v = c["body_bg"]
        lines += [f"--bg: {v};", f"--bg-body: {v};", f"--body-bg: {v};",
                  f"--bs-body-bg: {v};", f"--bs-body-bg-rgb: {rgb_triplet(v)};"]
    if c["text_color"]:
        v = c["text_color"]
        lines += [f"--text: {v};", f"--bs-body-color: {v};", f"--bs-body-color-rgb: {rgb_triplet(v)};",
                  f"--bs-heading-color: {v};"]
        if c["body_bg"]:
            lines.append(f"--text-secondary: {mix(v, c['body_bg'], 0.2)};")
    if c["text_muted"]:
        v = c["text_muted"]
        lines += [f"--text-muted: {v};", f"--bs-secondary-color: {v};"]
    if c["white"]:
        v = c["white"]
        lines += [f"--white: {v};", f"--bg-card: {v};", f"--card-bg: {v};", f"--glass-2: {v};",
                  f"--glass: rgba({rgb_triplet(v)}, 0.92);", f"--bs-card-bg: {v};",
                  f"--bs-tertiary-bg: {v};"]
    if c["light"]:
        v = c["light"]
        lines += [f"--light: {v};", f"--glass-soft: rgba({rgb_triplet(v)}, 0.72);",
                  f"--bs-light: {v};", f"--bs-light-rgb: {rgb_triplet(v)};"]
    if c["dark"]:
        v = c["dark"]
        lines += [f"--dark: {v};", f"--bs-dark: {v};", f"--bs-dark-rgb: {rgb_triplet(v)};"]
    if c["border"]:
        v = c["border"]
        lines += [f"--border: {v};", f"--glass-brd: {v};", f"--glass-brd-soft: {mix(v, '#ffffff', 0.35)};",
                  f"--bs-border-color: {v};"]
    return lines


def build_css(theme):
    """CSS variables pou tèm lan. Pa gen tèm => default yo nan brand.css rete."""
    if theme is None:
        return "/* no active theme */\n"

    shared = []
    font = (theme.font_family or "").strip()
    if FONT_RE.match(font):
        shared += [f"--font-family: {font};", f"--font-body: {font};", f"--bs-body-font-family: {font};"]
    radius = (theme.border_radius or "").strip()
    if LENGTH_RE.match(radius):
        shared += [f"--radius: {radius};", f"--bs-border-radius: {radius};"]
    shadow = (theme.box_shadow or "").strip()
    if SHADOW_RE.match(shadow):
        shared += [f"--shadow: {shadow};"]

    css = ["/* Généré par theme_manager — ne pas modifier à la main */",
           ":root {"]
    css += [f"  {line}" for line in _brand_vars(theme) + shared]
    css += ["}", ""]

    surfaces = _surface_vars(theme)
    if surfaces:
        # Mòd klè sèlman: pa janm kraze palèt fonse a
        css += [':root:not([data-theme="dark"]):not([data-bs-theme="dark"]) {']
        css += [f"  {line}" for line in surfaces]
        css += ["}", ""]

    # Mòd fonse: menm koulè mak yo, men pi klè (sinon brand.css fonse a ta rete ak koulè default li)
    css += ['html[data-theme="dark"], html[data-bs-theme="dark"], html.dark {']
    css += [f"  {line}" for line in _brand_vars(theme, dark=True)]
    css += ["}", ""]
    return "\n".join(css)


def css_version(theme):
    return hashlib.sha1(build_css(theme).encode("utf-8")).hexdigest()[:10]
