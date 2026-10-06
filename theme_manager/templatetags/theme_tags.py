"""
Filtè pou done tèm lan pase nan template yo san danje (XSS) e san HTML ki parèt kòm tèks.
{% load theme_tags %}
"""
import re
from html import escape
from html.parser import HTMLParser
from urllib.parse import urlparse

from django import template
from django.utils.html import format_html, linebreaks
from django.utils.safestring import mark_safe

from theme_manager.services import css_color as _css_color, safe_color

register = template.Library()

ALLOWED_TAGS = {
    "p", "br", "hr", "strong", "b", "em", "i", "u", "small", "span", "div",
    "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "code", "pre",
    "a", "img", "table", "thead", "tbody", "tr", "th", "td",
}
VOID_TAGS = {"br", "hr", "img"}
DROP_WITH_CONTENT = {"script", "style", "iframe", "object", "embed", "noscript", "template"}
ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "img": {"src", "alt", "title", "width", "height"},
    "th": {"colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
}
HAS_HTML_RE = re.compile(r"<\s*/?\s*[a-zA-Z][^>]*>")


def _safe_url(value, allow_mailto=False):
    value = (value or "").strip()
    if not value:
        return None
    if value.startswith(("/", "#")) and not value.startswith("//"):
        return value
    parsed = urlparse(value)
    schemes = {"http", "https"} | ({"mailto", "tel"} if allow_mailto else set())
    return value if parsed.scheme.lower() in schemes else None


class _Sanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.stack, self.skip_depth = [], [], 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_WITH_CONTENT:
            self.skip_depth += 1
            return
        if self.skip_depth or tag not in ALLOWED_TAGS:
            return
        parts = [tag]
        allowed = ALLOWED_ATTRS.get(tag, set())
        for name, value in attrs:
            name = (name or "").lower()
            if name not in allowed:
                continue
            if name == "href":
                value = _safe_url(value, allow_mailto=True)
            elif name == "src":
                value = _safe_url(value)
            if value is None:
                continue
            parts.append(f'{name}="{escape(value, quote=True)}"')
        if tag == "a":
            parts.append('rel="noopener noreferrer"')
        self.out.append("<" + " ".join(parts) + ">")
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in self.stack and tag not in VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth or tag not in ALLOWED_TAGS or tag in VOID_TAGS:
            return
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                self.out.append(f"</{top}>")
                if top == tag:
                    break

    def handle_data(self, data):
        if not self.skip_depth:
            self.out.append(escape(data, quote=False))

    def result(self):
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")
        return "".join(self.out)


@register.filter(name="rich_text")
def rich_text(value):
    """
    Tèks ki soti nan admin (FAQ, kondisyon, konfidansyalite, à propos).
    - Pa gen HTML  -> escape + paragraf/liy
    - Gen HTML     -> netwaye (lis tag/atribi pèmèt), pa janm <script>/onclick/javascript:
    """
    value = value or ""
    if not HAS_HTML_RE.search(value):
        return linebreaks(value, autoescape=True)
    sanitizer = _Sanitizer()
    sanitizer.feed(value)
    sanitizer.close()
    return mark_safe(sanitizer.result())


_MAP_SRC_RE = re.compile(r'src\s*=\s*["\']([^"\']+)["\']', re.I)
_MAP_ALLOWED_HOSTS = {"www.google.com", "maps.google.com", "google.com"}


@register.filter(name="embed_map")
def embed_map(value):
    """Aksepte kòd iframe Google Maps (oswa jis URL la) epi re-konstwi yon iframe san danje."""
    value = (value or "").strip()
    if not value:
        return ""
    match = _MAP_SRC_RE.search(value)
    url = match.group(1) if match else value
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in _MAP_ALLOWED_HOSTS or "/maps" not in parsed.path:
        return ""
    return format_html(
        '<iframe src="{}" class="map-embed" loading="lazy" allowfullscreen '
        'referrerpolicy="no-referrer-when-downgrade" title="Map"></iframe>',
        url,
    )


@register.filter(name="abs_url")
def abs_url(value, request):
    """URL absoli (menm si valè a deja absoli, pa double host la)."""
    if not value:
        return ""
    return request.build_absolute_uri(value)


@register.filter(name="hex_color")
def hex_color(value):
    """Koulè (hex, non tankou 'blue', rgb(), hsl()) -> #rrggbb, sinon vid."""
    return safe_color(value, "")


@register.filter(name="css_color")
def css_color(value):
    """'primary' | 'success' | 'blue' | '#0af' -> var(--primary) | var(--success) | #0000ff | #00aaff (sinon vid)."""
    return _css_color(value)
