"""Keep the dated official-product captures tied to their coverage lineage."""
import json
from pathlib import Path
import unittest
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'data/brand-md-monitoring/2026-10-12-onward-spring-month-evidence.json'


class OnwardEvidenceTests(unittest.TestCase):
    def test_dates_and_product_identity_are_bound_to_official_responses(self):
        report = json.loads((ROOT / REPORT).read_text(encoding='utf-8'))
        coverage = json.loads((ROOT / 'data/brand-md-monitoring/2026-spring-backfill-coverage.json').read_text(encoding='utf-8'))
        brands = {b['brand_id']: b for b in coverage['brand_month_coverage']}
        for change in report['verified_changes']:
            with self.subTest(change=change):
                code = change['product_code']
                capture = report['official_product_captures'][code]
                self.assertEqual(capture['brand_id'], change['brand_id'])
                self.assertEqual(capture['brand_name'], change['brand_name'])
                self.assertEqual(capture['gender'], 'WOMEN')
                self.assertIn(capture['category'], ('ニット/セーター', 'カーディガン'))
                self.assertEqual(capture['final_url'], 'https://crosset.onward.co.jp/items/' + code)
                fragment = urlsplit(capture['review_fragment_url'])
                self.assertEqual(fragment.hostname, 'crosset.onward.co.jp')
                self.assertEqual(parse_qs(fragment.query)['TP[itemCode]'], [code])
                self.assertEqual(capture['review_gender'], '性別:女性')
                self.assertIn(change['date'], capture['review_dates'] + capture['all_review_dates'])
                self.assertEqual(change['date'][:7], change['month'])
                for key in ('product_response_sha256', 'review_response_sha256'):
                    self.assertRegex(capture[key], r'^[a-f0-9]{64}$')
                cell = brands[change['brand_id']]['months'][change['month']]
                product = next(p for p in cell['verified_product_evidence'] if p['product_code'] == code)
                self.assertEqual(product['published_date'], change['date'])
                self.assertEqual(product['original_evidence_index'], change['original_evidence_index'])
                self.assertEqual(product['period_evidence']['source_capture_path'], REPORT)
                self.assertEqual(cell['evidence'][product['original_evidence_index']]['url'], product['url'])
                self.assertFalse(product['period_evidence']['sales_start_date_proven'])

    def test_capture_summary_does_not_confuse_products_cells_or_canonical_rows(self):
        report = json.loads((ROOT / REPORT).read_text(encoding='utf-8'))
        changes = report['verified_changes']
        self.assertEqual(len({(c['brand_id'], c['month']) for c in changes}), report['promoted_brand_month_cells'])
        self.assertEqual(len(changes), report['new_product_month_observations'])
        before, after = report['before_summary'], report['after_summary']
        self.assertEqual(after['terminal_brand_month_cells'] - before['terminal_brand_month_cells'], report['promoted_brand_month_cells'])
        self.assertEqual(after['verified_product_month_observations'] - before['verified_product_month_observations'], len(changes))
        self.assertEqual(after['terminal_brand_month_cells'] + after['pending_brand_month_cells'], 240)
        self.assertEqual(after['partial_brand_month_cells'] + after['not_started_brand_month_cells'], after['pending_brand_month_cells'])
        self.assertEqual(report['integrity']['canonical_ledger_rows_unchanged'], 2)
        self.assertEqual(report['publication_status'], 'PUBLISH_HOLD')
        self.assertTrue(report['human_review_required'])


if __name__ == '__main__':
    unittest.main()
