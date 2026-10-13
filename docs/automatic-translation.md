# Automatic French / Haitian Creole translation

The language selector posts the selected language and keeps the current URL.
When the selected page language is Haitian Creole (`ht`), the optional
`DynamicTranslationMiddleware` translates rendered HTML text, accessible labels,
placeholders, image alt text, and SEO descriptions. It skips scripts, styles,
code, preformatted blocks, textareas, non-HTML responses, and failed responses.

## Turn on automatic translation

1. Enable the Google Cloud Translation API (Basic v2) for a Google Cloud project
   and create an API key restricted to that API.
2. Add `GOOGLE_TRANSLATE_API_KEY` as a server-side environment secret in the
   deployment environment. Never commit the key or put it in browser code.
3. Redeploy the application.

Without the secret, the middleware is inactive and does not send page content
anywhere. When enabled, visible HTML text—including dynamic course data and
other text rendered on a page—is sent to Google Cloud Translation for
translation into Haitian Creole. Do not enable it for content that must not be
shared with that provider. Translation results are cached by the source text for
30 days in the configured Django cache (the default local-memory cache can be
cleared by a process restart); changed text has a different cache key and is
translated automatically.
Temporary provider errors return the original text and are retried after one
minute. Google Cloud Translation may incur charges.

The existing `titre_ht`, `description_ht`, and `texte_ht` fields remain usable;
the automatic layer also covers page content that has no hand-entered Kreyòl
field. Google Translate is only called for Haitian-Creole HTML responses.
