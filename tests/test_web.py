import unittest
from datetime import datetime, timedelta, timezone
from provider.web import (
    search_web, fetch_page, context_for_messages, WebError, _public_https,
    clock_context, augment_messages,
)


class WebTests(unittest.TestCase):
    def test_blocks_private_and_non_https(self):
        for url in ['http://example.com/', 'https://127.0.0.1/', 'https://localhost/x',
                    'https://user@example.com/', 'https://192.168.1.8/']:
            with self.assertRaises(WebError):
                _public_https(url)

    def test_search_parses_wikipedia_and_ddg(self):
        def opener(url):
            if 'wikipedia.org' in url:
                return b'{"query":{"search":[{"title":"Riyadh","snippet":"Capital of <span>Saudi</span> Arabia"}]}}'
            return b'{"Heading":"Riyadh","AbstractText":"Capital city.","AbstractURL":"https://example.com/r"}'
        hits = search_web('Riyadh news today', opener=opener)
        self.assertEqual(hits[0]['title'], 'Riyadh')
        self.assertIn('Capital city', hits[0]['snippet'])
        self.assertTrue(any('wiki' in h['url'] for h in hits))

    def test_fetch_strips_scripts(self):
        html = b'<html><script>secret()</script><p>Visible article</p></html>'
        text = fetch_page('https://example.com/a', opener=lambda url: html)
        self.assertIn('Visible article', text)
        self.assertNotIn('secret', text)

    def test_chat_context_uses_user_question(self):
        ctx = context_for_messages(
            [{'role': 'user', 'content': 'What is happening in Riyadh today?'}],
            search=lambda q: [{'title': 'Riyadh', 'url': 'https://example.com', 'snippet': 'Update'}],
            fetch=lambda url: 'ignored',
        )
        self.assertIn('Live web research', ctx)
        self.assertIn('Riyadh', ctx)

    def test_short_messages_skip_search(self):
        self.assertEqual(context_for_messages([{'role': 'user', 'content': 'ok'}], search=lambda q: [_ for _ in ()]), '')

    def test_clock_uses_supplied_now_not_training_cutoff(self):
        now = datetime(2026, 9, 18, 4, 23, tzinfo=timezone(timedelta(hours=3)))
        clock = clock_context(now)
        self.assertIn('2026-09-18', clock)
        self.assertIn('الجمعة', clock)
        self.assertNotIn('2024', clock)
        payload = augment_messages(
            [{'role': 'user', 'content': 'ما تاريخ اليوم؟'}],
            now=now,
            search=lambda q: [],
            fetch=lambda url: '',
        )
        self.assertEqual(payload[0]['role'], 'system')
        self.assertIn('2026-09-18', payload[0]['content'])
        self.assertEqual(payload[-1]['content'], 'ما تاريخ اليوم؟')

    def test_augment_includes_web_research(self):
        payload = augment_messages(
            [{'role': 'user', 'content': 'What is happening in Riyadh today?'}],
            now=datetime(2026, 9, 18, tzinfo=timezone.utc),
            search=lambda q: [{'title': 'Riyadh', 'url': 'https://example.com', 'snippet': 'Update'}],
            fetch=lambda url: 'ignored',
        )
        self.assertTrue(any('Live web research' in m['content'] for m in payload))


if __name__ == '__main__':
    unittest.main()
