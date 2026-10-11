"""Optional cached Google Cloud Translation for rendered HTML pages."""

import hashlib
import html
import logging
import re
from html.parser import HTMLParser

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import get_language


logger = logging.getLogger(__name__)
GOOGLE_TRANSLATE_URL = "https://translation.googleapis.com/language/translate/v2"
TRANSLATION_CACHE_SECONDS = 60 * 60 * 24 * 30
FAILED_TRANSLATION_CACHE_SECONDS = 60
MAX_BATCH_ITEMS = 100
MAX_BATCH_CHARACTERS = 25000

_SKIP_CONTENT_TAGS = {
    "code",
    "kbd",
    "noscript",
    "pre",
    "script",
    "style",
    "svg",
    "textarea",
}
_VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}
_TRANSLATABLE_ATTRIBUTES = {"alt", "aria-description", "aria-label", "placeholder", "title"}
_WORD_PATTERN = re.compile(r"[^\W\d_]", re.UNICODE)


def _cache_key(text, target_language):
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return f"educadim-auto-translation:{target_language}:{digest}"


def _split_whitespace(text):
    start = len(text) - len(text.lstrip())
    end = len(text.rstrip())
    return text[:start], text[start:end], text[end:]


def translate_texts(texts, target_language):
    """Translate a sequence of strings, returning originals if translation fails."""
    api_key = getattr(settings, "GOOGLE_TRANSLATE_API_KEY", "")
    originals = list(texts)
    if not api_key or not originals or target_language != "ht":
        return originals

    translated = list(originals)
    pending_by_key = {}
    for index, value in enumerate(originals):
        if not isinstance(value, str):
            continue
        prefix, core, suffix = _split_whitespace(value)
        if not core or not _WORD_PATTERN.search(core):
            continue
        key = _cache_key(core, target_language)
        cached = cache.get(key)
        if cached is not None:
            translated[index] = prefix + cached + suffix
        else:
            pending_by_key.setdefault(key, {"text": core, "indexes": []})["indexes"].append(index)

    if not pending_by_key:
        return translated

    pending = list(pending_by_key.items())
    for offset in range(0, len(pending), MAX_BATCH_ITEMS):
        chunk = []
        chunk_size = 0
        for item in pending[offset:offset + MAX_BATCH_ITEMS]:
            size = len(item[1]["text"])
            if chunk and chunk_size + size > MAX_BATCH_CHARACTERS:
                _translate_batch(chunk, target_language, api_key, translated)
                chunk = []
                chunk_size = 0
            chunk.append(item)
            chunk_size += size
        if chunk:
            _translate_batch(chunk, target_language, api_key, translated)

    return translated


def _translate_batch(items, target_language, api_key, output):
    """Translate one bounded batch and populate both the response and cache."""
    try:
        response = requests.post(
            GOOGLE_TRANSLATE_URL,
            params={"key": api_key},
            json={
                "q": [entry["text"] for _, entry in items],
                "target": target_language,
                "format": "text",
            },
            timeout=(2, 5),
        )
        response.raise_for_status()
        records = response.json()["data"]["translations"]
        if len(records) != len(items):
            raise ValueError("Translation provider returned an incomplete batch")
        for (key, entry), record in zip(items, records):
            # Google returns HTML-escaped text even when format="text".
            value = html.unescape(record.get("translatedText") or entry["text"])
            cache.set(key, value, TRANSLATION_CACHE_SECONDS)
            for index in entry["indexes"]:
                prefix, _, suffix = _split_whitespace(output[index])
                output[index] = prefix + value + suffix
    except (KeyError, TypeError, ValueError, requests.RequestException) as exc:
        # Do not log provider URLs or request content; the API key is in its URL.
        logger.warning("Automatic translation failed (%s)", type(exc).__name__)
        for key, entry in items:
            cache.set(key, entry["text"], FAILED_TRANSLATION_CACHE_SECONDS)


class _TranslatableHTMLParser(HTMLParser):
    """Collect visible text and user-facing labels while preserving page markup."""

    def __init__(self, content):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.texts = []
        self.skip_depth = 0
        self.feed(content)
        self.close()

    def _add_text(self, value):
        index = len(self.texts)
        self.texts.append(value)
        self.parts.append(("text", index))

    def _attribute_indexes(self, tag, attrs):
        attr_map = {name: value for name, value in attrs}
        translatable = []
        meta_labels = {
            "description", "keywords", "og:title", "og:description",
            "twitter:title", "twitter:description",
        }
        for name, value in attrs:
            if not value:
                continue
            if name in _TRANSLATABLE_ATTRIBUTES:
                translatable.append((name, len(self.texts)))
                self.texts.append(value)
            elif tag == "meta" and name == "content":
                label = attr_map.get("name") or attr_map.get("property") or ""
                if label.lower() in meta_labels:
                    translatable.append((name, len(self.texts)))
                    self.texts.append(value)
        return translatable

    def handle_starttag(self, tag, attrs):
        raw = self.get_starttag_text()
        if self.skip_depth:
            self.parts.append(("raw", raw))
            if tag not in _VOID_TAGS:
                self.skip_depth += 1
            return
        if tag in _SKIP_CONTENT_TAGS:
            self.parts.append(("raw", raw))
            self.skip_depth = 1
            return

        attr_indexes = self._attribute_indexes(tag, attrs)
        if attr_indexes:
            self.parts.append(("tag", tag, attrs, attr_indexes, False))
        else:
            self.parts.append(("raw", raw))

    def handle_startendtag(self, tag, attrs):
        if self.skip_depth or tag in _SKIP_CONTENT_TAGS:
            self.parts.append(("raw", self.get_starttag_text()))
            return
        attr_indexes = self._attribute_indexes(tag, attrs)
        if attr_indexes:
            self.parts.append(("tag", tag, attrs, attr_indexes, True))
        else:
            self.parts.append(("raw", self.get_starttag_text()))

    def handle_endtag(self, tag):
        self.parts.append(("raw", f"</{tag}>"))
        if self.skip_depth and tag not in _VOID_TAGS:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth:
            self.parts.append(("raw", data))
        else:
            self._add_text(data)

    def handle_comment(self, data):
        self.parts.append(("raw", f"<!--{data}-->"))

    def handle_decl(self, decl):
        self.parts.append(("raw", f"<!{decl}>"))

    def handle_entityref(self, name):
        self.parts.append(("raw", f"&{name};"))

    def handle_charref(self, name):
        self.parts.append(("raw", f"&#{name};"))

    def render(self, target_language):
        translated = translate_texts(self.texts, target_language)
        output = []
        for part in self.parts:
            if part[0] == "raw":
                output.append(part[1])
            elif part[0] == "text":
                output.append(html.escape(translated[part[1]], quote=False))
            else:
                _, tag, attrs, attr_indexes, self_closing = part
                translated_attrs = dict(attr_indexes)
                output.append("<" + tag)
                for name, value in attrs:
                    if value is None:
                        output.append(f" {name}")
                    else:
                        rendered_value = translated[translated_attrs[name]] if name in translated_attrs else value
                        output.append(f' {name}="{html.escape(rendered_value, quote=True)}"')
                output.append(" />" if self_closing else ">")
        return "".join(output)


class DynamicTranslationMiddleware:
    """Translate all rendered HTML to Haitian Creole when explicitly configured."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        api_key = getattr(settings, "GOOGLE_TRANSLATE_API_KEY", "")
        if (
            not api_key
            or get_language() != "ht"
            or getattr(response, "streaming", False)
            or response.status_code != 200
            or response.get("Content-Encoding")
            or "attachment" in response.get("Content-Disposition", "").lower()
            or not response.get("Content-Type", "").lower().startswith("text/html")
        ):
            return response

        try:
            source = response.content.decode(response.charset or "utf-8")
            parser = _TranslatableHTMLParser(source)
            response.content = parser.render("ht").encode(response.charset or "utf-8")
            if response.has_header("Content-Length"):
                response["Content-Length"] = str(len(response.content))
        except (UnicodeDecodeError, LookupError, ValueError) as exc:
            logger.warning("Could not translate HTML response (%s)", type(exc).__name__)
        return response
