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
NAMED_COLORS = {
    pair.split(":")[0]: "#" + pair.split(":")[1]
    for pair in "aliceblue:f0f8ff,antiquewhite:faebd7,aqua:00ffff,aquamarine:7fffd4,azure:f0ffff,beige:f5f5dc,bisque:ffe4c4,black:000000,blanchedalmond:ffebcd,blue:0000ff,blueviolet:8a2be2,brown:a52a2a,burlywood:deb887,cadetblue:5f9ea0,chartreuse:7fff00,chocolate:d2691e,coral:ff7f50,cornflowerblue:6495ed,cornsilk:fff8dc,crimson:dc143c,cyan:00ffff,darkblue:00008b,darkcyan:008b8b,darkgoldenrod:b8860b,darkgray:a9a9a9,darkgreen:006400,darkgrey:a9a9a9,darkkhaki:bdb76b,darkmagenta:8b008b,darkolivegreen:556b2f,darkorange:ff8c00,darkorchid:9932cc,darkred:8b0000,darksalmon:e9967a,darkseagreen:8fbc8f,darkslateblue:483d8b,darkslategray:2f4f4f,darkslategrey:2f4f4f,darkturquoise:00ced1,darkviolet:9400d3,deeppink:ff1493,deepskyblue:00bfff,dimgray:696969,dimgrey:696969,dodgerblue:1e90ff,firebrick:b22222,floralwhite:fffaf0,forestgreen:228b22,fuchsia:ff00ff,gainsboro:dcdcdc,ghostwhite:f8f8ff,gold:ffd700,goldenrod:daa520,gray:808080,green:008000,greenyellow:adff2f,grey:808080,honeydew:f0fff0,hotpink:ff69b4,indianred:cd5c5c,indigo:4b0082,ivory:fffff0,khaki:f0e68c,lavender:e6e6fa,lavenderblush:fff0f5,lawngreen:7cfc00,lemonchiffon:fffacd,lightblue:add8e6,lightcoral:f08080,lightcyan:e0ffff,lightgoldenrodyellow:fafad2,lightgray:d3d3d3,lightgreen:90ee90,lightgrey:d3d3d3,lightpink:ffb6c1,lightsalmon:ffa07a,lightseagreen:20b2aa,lightskyblue:87cefa,lightslategray:778899,lightslategrey:778899,lightsteelblue:b0c4de,lightyellow:ffffe0,lime:00ff00,limegreen:32cd32,linen:faf0e6,magenta:ff00ff,maroon:800000,mediumaquamarine:66cdaa,mediumblue:0000cd,mediumorchid:ba55d3,mediumpurple:9370db,mediumseagreen:3cb371,mediumslateblue:7b68ee,mediumspringgreen:00fa9a,mediumturquoise:48d1cc,mediumvioletred:c71585,midnightblue:191970,mintcream:f5fffa,mistyrose:ffe4e1,moccasin:ffe4b5,navajowhite:ffdead,navy:000080,oldlace:fdf5e6,olive:808000,olivedrab:6b8e23,orange:ffa500,orangered:ff4500,orchid:da70d6,palegoldenrod:eee8aa,palegreen:98fb98,paleturquoise:afeeee,palevioletred:db7093,papayawhip:ffefd5,peachpuff:ffdab9,peru:cd853f,pink:ffc0cb,plum:dda0dd,powderblue:b0e0e6,purple:800080,rebeccapurple:663399,red:ff0000,rosybrown:bc8f8f,royalblue:4169e1,saddlebrown:8b4513,salmon:fa8072,sandybrown:f4a460,seagreen:2e8b57,seashell:fff5ee,sienna:a0522d,silver:c0c0c0,skyblue:87ceeb,slateblue:6a5acd,slategray:708090,slategrey:708090,snow:fffafa,springgreen:00ff7f,steelblue:4682b4,tan:d2b48c,teal:008080,thistle:d8bfd8,tomato:ff6347,turquoise:40e0d0,violet:ee82ee,wheat:f5deb3,white:ffffff,whitesmoke:f5f5f5,yellow:ffff00,yellowgreen:9acd32".split(",")
}
RGB_FN_RE = re.compile(r"^rgba?\(\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*[, ]\s*(\d{1,3})\s*(?:[,/]\s*[\d.]+%?\s*)?\)$", re.I)
HSL_FN_RE = re.compile(r"^hsla?\(\s*(-?[\d.]+)(?:deg)?\s*[, ]\s*([\d.]+)%\s*[, ]\s*([\d.]+)%\s*(?:[,/]\s*[\d.]+%?\s*)?\)$", re.I)
SEMANTIC_NAMES = ("primary", "secondary", "success", "danger", "warning", "info", "light", "dark")


def _hsl_to_hex(h, s, l):
    import colorsys
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, max(0, min(1, l)), max(0, min(1, s)))
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def parse_color(value, default=None):
    """
    Aksepte TOUT sa admin ka tape pou yon koulè epi retounen yon hex #rrggbb:
      #fff, #ffffff, #ffffff80, blue, Red, rgb(0,0,255), rgba(0 0 255 / .5), hsl(220 90% 50%).
    Retounen `default` si pa konprann (jamè pa janm voye valè brut nan CSS).
    """
    v = (value or "").strip().rstrip(";").strip().lower()
    if not v:
        return default
    if v.startswith("#"):
        h = v[1:]
        if re.fullmatch(r"[0-9a-f]{3}", h):
            return "#" + "".join(ch * 2 for ch in h)
        if re.fullmatch(r"[0-9a-f]{6}", h):
            return "#" + h
        if re.fullmatch(r"[0-9a-f]{8}", h):
            return "#" + h[:6]          # inyore alfa
        if re.fullmatch(r"[0-9a-f]{4}", h):
            return "#" + "".join(ch * 2 for ch in h[:3])
        return default
    if v in NAMED_COLORS:
        return NAMED_COLORS[v]
    m = RGB_FN_RE.match(v)
    if m:
        r, g, b = (min(255, int(x)) for x in m.groups())
        return "#%02x%02x%02x" % (r, g, b)
    m = HSL_FN_RE.match(v)
    if m:
        return _hsl_to_hex(float(m.group(1)), float(m.group(2)) / 100, float(m.group(3)) / 100)
    return default


def safe_color(value, default=None):
    """Konpatib ak ansyen kòd: retounen hex valid la (kounye a aksepte tou non koulè)."""
    return parse_color(value, default)


def css_color(value):
    """
    Pou chan tankou 'Feature 1 - Couleur' kote admin ka mete 'primary', 'success'... OSWA yon koulè.
    Retounen yon valè CSS ki pa danjere: var(--primary) | #rrggbb | ''.
    """
    v = (value or "").strip().rstrip(";").strip().lower()
    if v in SEMANTIC_NAMES:
        return f"var(--{v})"
    return parse_color(v, "") or ""


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
    first = (font_family or "").strip().rstrip(";").split(",")[0].strip().strip("'\"")
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
    # Fon paj nan mòd KLÈ = koulè "Clair" nan theme manager (si li pa valid -> "Fond de page")
    page_bg = c["light"] or c["body_bg"]
    if page_bg:
        v = page_bg
        lines += [f"--bg: {v};", f"--bg-body: {v};", f"--body-bg: {v};",
                  f"--bs-body-bg: {v};", f"--bs-body-bg-rgb: {rgb_triplet(v)};",
                  f"--light-tint-1: {mix(v, safe_color(getattr(theme, 'primary', None), '#176b91'), 0.08)};",
                  f"--light-tint-2: {mix(v, safe_color(getattr(theme, 'secondary', None), '#45b7c7'), 0.06)};"]
    if c["text_color"]:
        v = c["text_color"]
        lines += [f"--text: {v};", f"--bs-body-color: {v};", f"--bs-body-color-rgb: {rgb_triplet(v)};",
                  f"--bs-heading-color: {v};"]
        if page_bg:
            lines.append(f"--text-secondary: {mix(v, page_bg, 0.2)};")
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


def _dark_surface_vars(theme):
    """
    Mòd FONSE : fon paj = koulè "Foncé" (dark) nan theme manager.
    Kat, bordi ak nuans (hero, footer) kalkile ladan l ak primary/secondary,
    pou yo swiv admin lan olye de koulè fiks yo nan brand.css.
    """
    dark = safe_color(getattr(theme, "dark", None))
    if not dark:
        return []
    primary = safe_color(getattr(theme, "primary", None), "#176b91")
    secondary = safe_color(getattr(theme, "secondary", None), "#45b7c7")
    card = mix(dark, "#ffffff", 0.06)
    soft = mix(dark, "#ffffff", 0.10)
    border = mix(dark, "#ffffff", 0.16)
    return [
        f"--bg: {dark};", f"--bg-body: {dark};", f"--body-bg: {dark};",
        f"--bs-body-bg: {dark};", f"--bs-body-bg-rgb: {rgb_triplet(dark)};",
        f"--bg-card: {card};", f"--card-bg: {card};", f"--bs-card-bg: {card};",
        f"--bs-tertiary-bg: {card};", f"--glass-2: {card};",
        f"--glass: rgba({rgb_triplet(card)}, 0.85);",
        f"--glass-soft: rgba({rgb_triplet(soft)}, 0.65);",
        f"--border: {border};", f"--glass-brd: {border};", f"--glass-brd-soft: {border};",
        f"--bs-border-color: {border};",
        f"--dark-tint-1: {mix(dark, primary, 0.22)};",
        f"--dark-tint-2: {mix(dark, secondary, 0.16)};",
        f"--dark-tint-footer: {mix(dark, primary, 0.10)};",
    ]


def build_css(theme):
    """CSS variables pou tèm lan. Pa gen tèm => default yo nan brand.css rete."""
    if theme is None:
        return "/* no active theme */\n"

    shared = []
    font = (theme.font_family or "").strip().rstrip(";").strip()
    if FONT_RE.match(font):
        shared += [f"--font-family: {font};", f"--font-body: {font};", f"--bs-body-font-family: {font};"]
    radius = (theme.border_radius or "").strip().rstrip(";").strip()
    if LENGTH_RE.match(radius):
        shared += [f"--radius: {radius};", f"--bs-border-radius: {radius};"]
    shadow = (theme.box_shadow or "").strip().rstrip(";").strip()
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
    css += [f"  {line}" for line in _dark_surface_vars(theme)]
    css += ["}", ""]
    return "\n".join(css)


def css_version(theme):
    return hashlib.sha1(build_css(theme).encode("utf-8")).hexdigest()[:10]
