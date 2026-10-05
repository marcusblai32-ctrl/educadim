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
    # (nom variab, champ modèl, default, pa gen -hover nan model la)
    ("primary", "primary", "#5b76f7"),
    ("secondary", "secondary", "#22d3ee"),
    ("success", "success", "#22c55e"),
    ("danger", "danger", "#f43f5e"),
    ("warning", "warning", "#f59e0b"),
    ("info", "info", "#38bdf8"),
]


def _brand_vars(theme):
    lines = []
    for name, field, default in _BRAND:
        base = safe_color(getattr(theme, field, None), default)
        hover = safe_color(getattr(theme, f"{field}_hover", None), darken(base, 0.1))
        lines += [
            f"--{name}: {base};",
            f"--{name}-hover: {hover};",
            f"--{name}-light: {lighten(base, 0.3)};",
            f"--{name}-lighter: {lighten(base, 0.65)};",
            f"--{name}-dark: {darken(base, 0.18)};",
            f"--{name}-darker: {darken(base, 0.38)};",
            f"--{name}-rgb: {rgb_triplet(base)};",
            f"--on-{name}: {on_color(base)};",
        ]
    return lines


def build_css(theme):
    """CSS variables pou tèm lan. Pa gen tèm => default yo nan variables.css rete."""
    if theme is None:
        return "/* no active theme */\n"

    root = _brand_vars(theme)

    font = (theme.font_family or "").strip()
    if FONT_RE.match(font):
        root += [f"--font-family: {font};", f"--font-body: {font};"]

    radius = (theme.border_radius or "").strip()
    if LENGTH_RE.match(radius):
        root += [f"--radius: {radius};"]

    shadow = (theme.box_shadow or "").strip()
    if SHADOW_RE.match(shadow):
        root += [f"--shadow: {shadow};"]

    root += ["--body-bg: var(--bg-body);"]

    light = []
    mapping = [
        ("--bg-body", "body_bg"),
        ("--text", "text_color"),
        ("--text-muted", "text_muted"),
        ("--white", "white"),
        ("--light", "light"),
        ("--dark", "dark"),
        ("--border", "border"),
    ]
    values = {}
    for var, field in mapping:
        color = safe_color(getattr(theme, field, None))
        if color:
            values[var] = color
            light.append(f"{var}: {color};")
    if "--text" in values and "--bg-body" in values:
        light.append(f"--text-secondary: {mix(values['--text'], values['--bg-body'], 0.2)};")

    css = ["/* Généré par theme_manager — ne pas modifier à la main */", ":root {"]
    css += [f"  {line}" for line in root]
    css += ["}", ""]
    if light:
        # Mòd klè sèlman: pa janm kraze [data-theme="dark"]
        css += [':root:not([data-theme="dark"]) {']
        css += [f"  {line}" for line in light]
        css += ["}", ""]
    return "\n".join(css)


def css_version(theme):
    return hashlib.sha1(build_css(theme).encode("utf-8")).hexdigest()[:10]
