import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_spring_backfill_coverage import validate


class CoverageIntegrityTests(unittest.TestCase):
    def setUp(self):
        def read(path):
            return json.loads((ROOT / path).read_text(encoding='utf-8'))
        self.coverage = read('data/brand-md-monitoring/2026-spring-backfill-coverage.json')
        self.config = read('config/brand64-md-monitoring.json')
        self.ledger = read(self.config['retrospective_season_backfill']['ledger_path'])

    def run_validation(self):
        return validate(self.coverage, self.config, self.ledger)

    def cell(self, brand, month):
        return next(b for b in self.coverage['brand_month_coverage'] if b['brand_id'] == brand)['months'][month]

    def test_corrected_repository_data(self):
        self.assertEqual(self.run_validation()['pending_brand_month_cells'], 234)

    def test_feature_only_cannot_close_month(self):
        self.cell('BR-00035', '2026-01')['status'] = 'VERIFIED_PRODUCTS'
        with self.assertRaisesRegex(AssertionError, 'terminal product cell'):
            self.run_validation()

    def test_duplicate_feature_url_does_not_inflate_pages(self):
        self.cell('BR-00035', '2026-01')['official_pages_checked'] = 2
        with self.assertRaisesRegex(AssertionError, 'page count'):
            self.run_validation()

    def test_may_names_are_supplementary_two_not_verified_products(self):
        cell = self.cell('BR-00035', '2026-05')
        self.assertEqual(cell['supplementary_named_product_count'], 2)
        self.assertEqual(cell['verified_product_count'], 0)

    def test_brand_mismatch_rejected(self):
        self.cell('BR-00018', '2026-01')['verified_product_evidence'][0]['brand_id'] = 'BR-00052'
        with self.assertRaisesRegex(AssertionError, 'brand mismatch'):
            self.run_validation()

    def test_nonaccepted_source_rejected(self):
        self.cell('BR-00018', '2026-01')['verified_product_evidence'][0]['source_kind'] = 'OFFICIAL_BLOG'
        with self.assertRaisesRegex(AssertionError, 'feature-only'):
            self.run_validation()

    def test_wrong_month_rejected(self):
        self.cell('BR-00018', '2026-01')['verified_product_evidence'][0]['published_date'] = '2026-02-01'
        with self.assertRaisesRegex(AssertionError, 'month evidence'):
            self.run_validation()

    def test_product_count_cannot_count_feature_names(self):
        self.cell('BR-00035', '2026-05')['verified_product_count'] = 2
        with self.assertRaisesRegex(AssertionError, 'product count'):
            self.run_validation()

    def test_future_check_rejected(self):
        self.cell('BR-00018', '2026-01')['last_checked_at'] = '2099-01-01T00:00:00+09:00'
        with self.assertRaisesRegex(AssertionError, 'future check'):
            self.run_validation()

    def test_impossible_original_time_stays_invalid_after_clock_passes(self):
        cell = self.cell('BR-00035', '2026-01')
        cell['last_checked_at'] = cell['check_time_audit']['original_last_checked_at']
        self.coverage['last_updated_at'] = '2099-01-01T00:00:00Z'
        from datetime import datetime, timezone
        with self.assertRaisesRegex(AssertionError, 'invalid original'):
            validate(self.coverage, self.config, self.ledger, now=datetime(2100, 1, 1, tzinfo=timezone.utc))

    def test_stale_summary_rejected(self):
        self.coverage['summary']['terminal_brand_month_cells'] = 112
        with self.assertRaisesRegex(AssertionError, 'stale summary'):
            self.run_validation()

    def test_duplicate_product_identity_rejected(self):
        cell = self.cell('BR-00018', '2026-06')
        cell['verified_product_evidence'][1] = copy.deepcopy(cell['verified_product_evidence'][0])
        with self.assertRaisesRegex(AssertionError, 'duplicate product'):
            self.run_validation()

    def test_hold_cannot_be_released(self):
        self.coverage['publication_status'] = 'PUBLISHED'
        with self.assertRaises(AssertionError):
            self.run_validation()

    def test_no_products_requires_evidence(self):
        cell = self.cell('BR-00035', '2026-01')
        cell['status'] = 'VERIFIED_NO_PRODUCTS'
        with self.assertRaisesRegex(AssertionError, 'no-products'):
            self.run_validation()


if __name__ == '__main__':
    unittest.main()
