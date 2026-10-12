import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_spring_backfill_coverage import validate_no_products


class NoProductsEvidenceTests(unittest.TestCase):
    """Synthetic archive fixtures exercise the contract; they are not research data."""
    def setUp(self):
        self.brand = {'brand_id': 'BR-00001', 'brand_name': 'UNIQLO'}
        self.official_url = 'https://www.uniqlo.com/jp/ja/women/tops/knit'
        self.now = datetime(2026, 10, 12, tzinfo=timezone.utc)
        self.item = {
            **self.brand, 'source_kind': 'OFFICIAL_MONTH_ARCHIVE',
            'url': 'https://www.uniqlo.com/unit-test-only/archive/2026-02',
            'product_scope': 'WOMEN_KNIT', 'month': '2026-02',
            'period_start': '2026-02-01', 'period_end': '2026-02-28',
            'source_status': 'ONLINE', 'inspection_scope': 'COMPLETE_MONTH',
            'result': 'NO_WOMEN_KNIT_PRODUCTS', 'qualifying_product_count': 0,
            'checked_at': '2026-10-11T00:00:00Z',
            'observed_fact': 'Synthetic complete-month archive with no qualifying items.',
        }
        self.cell = {
            'last_checked_at': '2026-10-11T00:00:00Z', 'unresolved_reason': None,
            'no_products_evidence': [self.item],
            'evidence': [copy.deepcopy(self.item)],
            'evidence_audit': [{'evidence_index': 0, 'live_content_retrieved': True,
                                'brand_verification': 'MATCH_CONFIRMED',
                                'month_verification': 'COMPLETE_MONTH_ARCHIVE_CONFIRMED'}],
        }

    def validate(self):
        validate_no_products(self.cell, self.brand, '2026-02', self.official_url, self.now)

    def test_structured_complete_official_archive_contract(self):
        self.validate()

    def test_missing_cell_check_time(self):
        self.cell['last_checked_at'] = None
        with self.assertRaisesRegex(AssertionError, 'actual check time'):
            self.validate()

    def test_missing_evidence_check_time(self):
        self.item.pop('checked_at')
        with self.assertRaisesRegex(AssertionError, 'evidence check time'):
            self.validate()

    def test_future_evidence_check_time(self):
        self.item['checked_at'] = '2099-01-01T00:00:00Z'
        with self.assertRaisesRegex(AssertionError, 'evidence check time'):
            self.validate()

    def test_check_before_month_end_cannot_prove_zero(self):
        self.item['checked_at'] = '2026-02-20T00:00:00Z'
        with self.assertRaisesRegex(AssertionError, 'before the month ended'):
            self.validate()

    def test_access_limited_and_offline_are_not_no_products(self):
        for status in ('SOURCE_ACCESS_LIMITED', 'SOURCE_OFFLINE', 'SOURCE_OFFLINE_UNVERIFIED'):
            with self.subTest(status=status):
                self.item['source_status'] = status
                with self.assertRaisesRegex(AssertionError, 'access or completeness'):
                    self.validate()

    def test_unrelated_brand(self):
        self.item['brand_id'] = 'BR-99999'
        with self.assertRaisesRegex(AssertionError, 'brand mismatch'):
            self.validate()

    def test_wrong_month(self):
        self.item['month'] = '2026-03'
        with self.assertRaisesRegex(AssertionError, 'scope/month'):
            self.validate()

    def test_incomplete_month(self):
        self.item['period_end'] = '2026-02-27'
        with self.assertRaisesRegex(AssertionError, 'whole month'):
            self.validate()

    def test_unofficial_host(self):
        self.item['url'] = 'https://uniqlo.com.example.org/archive'
        with self.assertRaisesRegex(AssertionError, 'approved official host'):
            self.validate()

    def test_source_lineage_required(self):
        self.cell['evidence'] = []
        with self.assertRaisesRegex(AssertionError, 'source lineage'):
            self.validate()

    def test_archive_retrieval_required(self):
        self.cell['evidence_audit'][0]['live_content_retrieved'] = False
        with self.assertRaisesRegex(AssertionError, 'archive retrieval'):
            self.validate()

    def test_nonzero_results_cannot_be_no_products(self):
        self.item['qualifying_product_count'] = 1
        with self.assertRaisesRegex(AssertionError, 'result mismatch'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
