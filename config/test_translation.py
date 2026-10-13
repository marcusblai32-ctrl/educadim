from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.utils.translation import override

from config.translation import DynamicTranslationMiddleware


class DynamicTranslationMiddlewareTests(SimpleTestCase):
    @override_settings(GOOGLE_TRANSLATE_API_KEY="test-key")
    @patch("config.translation.requests.post")
    def test_translates_visible_content_and_labels_but_not_code(self, post):
        provider_response = Mock()
        provider_response.json.return_value = {
            "data": {"translations": [{"translatedText": "Bonjou"}]}
        }
        post.return_value = provider_response
        source = (
            '<html><body><h1 title="Bonjour">Bonjour</h1>'
            '<script>const message = "Bonjour";</script>'
            "<textarea>Bonjour</textarea></body></html>"
        )
        request = RequestFactory().get("/ht/cours/")
        middleware = DynamicTranslationMiddleware(lambda _: HttpResponse(source))

        with override("ht"):
            response = middleware(request)

        self.assertIn('<h1 title="Bonjou">Bonjou</h1>', response.content.decode())
        self.assertIn('<script>const message = "Bonjour";</script>', response.content.decode())
        self.assertIn("<textarea>Bonjour</textarea>", response.content.decode())
        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.kwargs["json"]["target"], "ht")

    @override_settings(GOOGLE_TRANSLATE_API_KEY="")
    @patch("config.translation.requests.post")
    def test_does_not_change_or_send_page_content_without_opt_in(self, post):
        source = "<html><body><p>Contni dinamik</p></body></html>"
        request = RequestFactory().get("/ht/cours/")
        middleware = DynamicTranslationMiddleware(lambda _: HttpResponse(source))

        with override("ht"):
            response = middleware(request)

        self.assertEqual(response.content.decode(), source)
        post.assert_not_called()

    @override_settings(GOOGLE_TRANSLATE_API_KEY="test-key")
    @patch("config.translation.requests.post")
    def test_new_or_changed_content_is_translated_as_a_new_source(self, post):
        provider_response = Mock()
        provider_response.raise_for_status.return_value = None

        def provider_reply(url, *, json, **kwargs):
            provider_response.json.return_value = {
                "data": {
                    "translations": [
                        {"translatedText": f"Kreyòl: {text}"}
                        for text in json["q"]
                    ]
                }
            }
            return provider_response

        post.side_effect = provider_reply
        request = RequestFactory().get("/ht/cours/")
        middleware = DynamicTranslationMiddleware(
            lambda _: HttpResponse("<p>Nouveau contenu de cours</p>")
        )

        with override("ht"):
            first = middleware(request).content.decode()
            second = DynamicTranslationMiddleware(
                lambda _: HttpResponse("<p>Contenu mis à jour</p>")
            )(request).content.decode()

        self.assertIn("Kreyòl: Nouveau contenu de cours", first)
        self.assertIn("Kreyòl: Contenu mis à jour", second)
        self.assertEqual(post.call_count, 2)
