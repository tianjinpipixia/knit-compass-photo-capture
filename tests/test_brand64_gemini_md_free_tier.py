import importlib.util
import io
import json
import pathlib
import unittest
from unittest.mock import patch
import urllib.error

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('gemini_md', ROOT / 'scripts/run_brand64_gemini_md_free_tier.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class GeminiMdFreeTierTests(unittest.TestCase):
    def test_call_uses_url_context_without_google_search(self):
        raw = {
            'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': '{"brands": []}'}]}}],
            'usageMetadata': {'totalTokenCount': 10},
        }
        fake = io.BytesIO(json.dumps(raw).encode())
        with patch.object(mod.urllib.request, 'urlopen', return_value=fake) as urlopen:
            result = mod.call_gemini('key', 'gemini-2.5-flash-lite', 'prompt', retry_429_seconds=0)
        payload = json.loads(urlopen.call_args.args[0].data)
        self.assertEqual(payload['tools'], [{'url_context': {}}])
        self.assertNotIn('google_search', json.dumps(payload))
        self.assertEqual(result['parsed']['brands'], [])

    def test_429_is_retried_once_then_aborts(self):
        def err():
            return urllib.error.HTTPError(
                'https://example.invalid', 429, 'quota', {}, io.BytesIO(b'{"error":{"status":"RESOURCE_EXHAUSTED"}}')
            )
        with patch.object(mod.time, 'sleep') as sleep, patch.object(mod.urllib.request, 'urlopen', side_effect=[err(), err()]):
            with self.assertRaises(mod.QuotaExhausted):
                mod.call_gemini('key', 'gemini-2.5-flash-lite', 'prompt', retry_429_seconds=0)
        self.assertEqual(sleep.call_count, 1)

    def test_priority_brands_sort_first(self):
        sources = {
            'BR-00001': {'brand_name': 'UNIQLO', 'entry_urls': ['https://example.com/uniqlo']},
            'BR-00065': {'brand_name': 'GALLARDAGALANTE', 'entry_urls': ['https://example.com/pal']},
            'BR-00075': {'brand_name': 'ZARA', 'entry_urls': ['https://example.com/zara']},
        }
        rows = mod.select_candidates(sources, {}, 3)
        self.assertEqual([x['brand_id'] for x in rows[:2]], ['BR-00065', 'BR-00075'])


if __name__ == '__main__':
    unittest.main()
