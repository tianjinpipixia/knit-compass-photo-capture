"""Bind the supplied official recheck to retained product/month evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'data/brand-md-monitoring/'
REPORT = PREFIX + '2026-10-14-shoo-spring-month-revalidation.json'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def digest(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


class ShooEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = read(REPORT)
        self.original = read(self.report['previous_report'])
        self.coverage = read(PREFIX + '2026-spring-backfill-coverage.json')
        self.brand = next(b for b in self.coverage['brand_month_coverage'] if b['brand_id'] == 'BR-00014')

    def test_seven_individual_women_knit_pages_match_product_numbers(self):
        expected = {'BRC6226S0016': 'C62-15300', 'BRC6226S0022': 'C62-15006',
                    'BRC6226S0184': 'C62-15325', 'BRC6226S0121': 'C62-15020',
                    'BRC6226S0241': 'C62-15317', 'BRC6226S0102': 'C62-15331',
                    'BRC6226S0356': 'C62-15350'}
        products = self.report['official_products']
        self.assertEqual({p['product_code']: p['world_item_code'] for p in products}, expected)
        for product in products:
            code = product['product_code']
            self.assertEqual(product['official_url'], 'https://store.world.co.jp/brand/shoo-la-rue/item/' + code)
            self.assertTrue(product['brand_confirmed'] and product['women_knit_confirmed'])
            self.assertEqual(self.original['official_product_captures'][code]['world_item_code'], product['world_item_code'])

    def test_twelve_unique_product_months_retain_direct_dated_lineage(self):
        rows = self.report['observations']
        self.assertEqual(len(rows), 12)
        self.assertEqual(len({(r['month'], r['product_code']) for r in rows}), 12)
        self.assertEqual(dict(Counter(r['month'] for r in rows)),
                         {'2026-01': 2, '2026-02': 2, '2026-03': 4, '2026-04': 1, '2026-05': 1, '2026-06': 2})
        for row in rows:
            cell = self.brand['months'][row['month']]
            product = next(p for p in cell['verified_product_evidence'] if p['product_code'] == row['product_code'])
            self.assertEqual(product['url'], row['official_product_url'])
            self.assertEqual(product['published_date'], row['observed_date'])
            self.assertEqual(row['observed_date'][:7], row['month'])
            self.assertEqual(product['period_evidence']['source_url'], row['dated_source_url'])
            self.assertEqual(product['period_evidence']['value'], row['observed_date'])
            self.assertEqual(cell['evidence'][row['original_evidence_index']]['url'], product['url'])
            self.assertFalse(product['period_evidence']['sales_start_date_proven'])
            self.assertTrue(row['qualifying_product_and_month_confirmed'])

    def test_live_introductions_and_publication_dates_are_distinct_from_rankings(self):
        live = [r for r in self.report['observations'] if r['date_kind'] == 'OFFICIAL_PRODUCT_BODY_LIVE_INTRODUCTION']
        self.assertEqual({r['observed_date'] for r in live}, {'2026-01-08', '2026-01-29', '2026-04-09'})
        self.assertEqual(self.report['article_publication_dates']['088966'], '2026-02-13')
        self.assertEqual(self.report['article_ranking_dates']['088966'], '2026-02-12')
        self.assertEqual(self.report['article_publication_dates']['092005'], '2026-05-25')
        self.assertEqual(self.report['article_publication_dates']['092355'], '2026-06-05')

    def test_corrections_are_appended_without_erasing_old_dates_or_reasons(self):
        expected = {'088953': ('2026-02-13', '2026-02-09'), '089849': ('2026-03-19', '2026-03-20')}
        for article, (old_date, corrected) in expected.items():
            correction = next(c for c in self.report['corrections_reconfirmed'] if article in c['article_url'])
            self.assertEqual((correction['old_recorded_date'], correction['confirmed_date']), (old_date, corrected))
            month = corrected[:7]
            originals = [r for r in self.brand['months'][month]['evidence'] if r['url'] == correction['article_url']]
            self.assertTrue(any(r.get('published_date') == old_date for r in originals))
        refs = self.original['subsequent_revalidations']
        self.assertTrue(any(r['report_path'] == REPORT for r in refs))

    def test_all_298_previous_evidence_and_audit_rows_remain_intact(self):
        inventory = read(PREFIX + '2026-spring-evidence-inventory-20261012.json')
        counts = Counter((r['brand_id'], r['month']) for r in inventory['entries'][:298])
        for field, snapshot in self.report['original_evidence_and_audit_preservation'].items():
            groups = []
            for brand in self.coverage['brand_month_coverage']:
                for month, cell in brand['months'].items():
                    count = counts[(brand['brand_id'], month)]
                    if count:
                        groups.append({'brand_id': brand['brand_id'], 'month': month, 'field': field,
                                       'prior_rows': count, 'sha256': digest(cell[field][:count])})
            self.assertEqual(sum(g['prior_rows'] for g in groups), snapshot['prior_rows'])
            self.assertEqual(snapshot['prior_rows'], 298)
            self.assertEqual(len(groups), snapshot['prefix_groups'])
            self.assertEqual(digest(groups), snapshot['prefix_group_sha256'])

    def test_summary_separates_qualifying_cells_observations_and_ledger(self):
        before, after = self.report['before_summary'], self.report['validated_candidate_summary']
        self.assertEqual(after['terminal_brand_month_cells'] - before['terminal_brand_month_cells'], 6)
        self.assertEqual(after['verified_product_month_observations'] - before['verified_product_month_observations'], 12)
        self.assertEqual(after['partial_brand_month_cells'], before['partial_brand_month_cells'] - 6)
        self.assertEqual(after['not_started_brand_month_cells'], before['not_started_brand_month_cells'])
        self.assertEqual(after['total_brand_month_cells'], 240)
        self.assertEqual(after['status'], 'INCOMPLETE')
        self.assertEqual(self.coverage['canonical_record_count'], self.report['canonical_ledger_records'])
        self.assertEqual(self.report['canonical_ledger_records'], 2)
        self.assertFalse(self.report['canonical_ledger_modified'])
        self.assertEqual(self.report['publication_status'], 'PUBLISH_HOLD')
        self.assertTrue(self.report['human_review_required'])
        excluded = set(self.report['unverified_product_codes_excluded'])
        self.assertFalse(excluded & {r['product_code'] for r in self.report['observations']})


if __name__ == '__main__':
    unittest.main()
