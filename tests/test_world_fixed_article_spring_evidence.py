"""Guard fixed-body dates, product identity and append-only WORLD evidence."""
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_spring_backfill_coverage import validate

REPORT = 'data/brand-md-monitoring/2026-10-14-opaque-index-spring-month-evidence.json'


def read(path):
    return json.loads((ROOT / path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


class WorldFixedArticleEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.report = read(REPORT)
        self.coverage = read('data/brand-md-monitoring/2026-spring-backfill-coverage.json')
        self.brands = {b['brand_id']: b for b in self.coverage['brand_month_coverage']}
        self.config = read('config/brand64-md-monitoring.json')
        policy = self.config['retrospective_season_backfill']
        self.ledger = read(policy['ledger_path'])
        self.inventory = read(policy['evidence_inventory_path'])
        self.refs = dict(approved_roster=read(policy['approved_roster_path']),
                         evidence_inventory=self.inventory, original_audit=read(policy['original_integrity_audit_path']))

    def check_coverage(self):
        return validate(self.coverage, self.config, self.ledger, **self.refs)

    def new_product(self):
        return self.brands['BR-00012']['months']['2026-03']['verified_product_evidence'][0]

    def test_exact_eight_cells_nine_observations_and_eight_distinct_identities(self):
        rows = self.report['observations']
        self.assertEqual(len(rows), 9)
        self.assertEqual(len({(r['brand_id'], r['month']) for r in rows}), 8)
        self.assertEqual(len({(r['brand_id'], r['month'], r['product_code']) for r in rows}), 9)
        self.assertEqual(len({r['product_code'] for r in rows}), 8)
        self.assertEqual(self.report['by_brand']['BR-00012'],
                         {'new_cells': 5, 'new_product_month_observations': 6, 'new_unique_products': 5})
        self.assertEqual(self.report['by_brand']['BR-00013'],
                         {'new_cells': 3, 'new_product_month_observations': 3, 'new_unique_products': 3})

    def test_individual_pages_numbers_and_dated_fixed_body_links_are_bound(self):
        expected = {'BRN0225F0006': 'N02-14001', 'BR63726S0084': '637-15069',
                    'BR63726S0200': '637-15136', 'BR63726S0080': '637-15003',
                    'BR63726S0311': '637-15165', 'BRC5826S0085': 'C58-15026',
                    'BRC5826S0127': 'C58-15041', 'BRC5826S0173': 'C58-15042'}
        self.assertEqual({p['product_code']: p['world_item_code'] for p in self.report['official_products']}, expected)
        for row in self.report['observations']:
            with self.subTest(code=row['product_code'], month=row['month']):
                cell = self.brands[row['brand_id']]['months'][row['month']]
                product = next(p for p in cell['verified_product_evidence'] if p['product_code'] == row['product_code'])
                self.assertEqual(product['source_kind'], 'OFFICIAL_PRODUCT_PAGE')
                self.assertEqual(product['world_item_code'], expected[row['product_code']])
                slug = 'opaque-clip' if row['brand_id'] == 'BR-00012' else 'index'
                self.assertEqual(product['url'], f"https://store.world.co.jp/brand/{slug}/item/{row['product_code']}")
                period = product['period_evidence']
                self.assertEqual(period, row['period_evidence'])
                self.assertEqual(period['kind'], 'OFFICIAL_DATED_ARTICLE_PRODUCT_MATCH')
                self.assertEqual(period['article_region'], 'FIXED_BODY')
                self.assertIs(period['direct_link_confirmed'], True)
                self.assertEqual(period['article_product_id'], row['product_code'])
                self.assertEqual(period['value'], row['observed_date'])
                self.assertEqual(period['value'][:7], row['month'])
                self.assertEqual(period['source_capture_path'], REPORT)
                self.assertEqual(urlsplit(period['source_url']).hostname, 'store.world.co.jp')
                self.assertIs(period['sales_start_date_proven'], False)
                self.assertTrue(all(product[k] is True for k in ['brand_verified', 'knit_verified', 'gender_verified', 'month_verified']))
                self.assertEqual(cell['evidence'][product['original_evidence_index']]['url'], product['url'])
                article = cell['evidence'][product['original_article_evidence_index']]
                self.assertEqual((article['url'], article['published_date'], article['article_region']),
                                 (period['source_url'], period['value'], 'FIXED_BODY'))

    def test_publication_dates_and_color_link_ids_do_not_become_extra_products(self):
        expected = [('BRN0225F0006', '2026-01-09', '087888', '101'),
                    ('BR63726S0084', '2026-02-09', '088953', '101'),
                    ('BR63726S0200', '2026-03-20', '089849', '102'),
                    ('BR63726S0080', '2026-03-20', '089849', '103'),
                    ('BR63726S0311', '2026-05-25', '092005', '103'),
                    ('BR63726S0311', '2026-06-05', '092355', '107'),
                    ('BRC5826S0085', '2026-02-13', '088966', '101'),
                    ('BRC5826S0127', '2026-03-20', '089849', '104'),
                    ('BRC5826S0173', '2026-05-25', '092005', '103')]
        actual = [(r['product_code'], r['observed_date'], r['period_evidence']['source_url'].rstrip('/').split('/')[-1],
                   r['period_evidence']['article_link_color_ids'][0]) for r in self.report['observations']]
        self.assertEqual(actual, expected)
        february = next(r for r in self.report['observations'] if r['product_code'] == 'BRC5826S0085')
        self.assertEqual(february['period_evidence']['ranking_created_date'], '2026-02-12')

    def test_set_components_are_not_merged_or_counted_as_two_identities(self):
        material = self.report['component_materials']['BR63726S0200']
        self.assertEqual(material['count_as_product_identities'], 1)
        self.assertFalse(material['aggregate_blend_calculated'])
        self.assertFalse(material['component_weight_ratios_known'])
        self.assertEqual(material['components']['knit_pullover'], {'polyester': 38, 'viscose': 25, 'acrylic': 19, 'cotton': 18})
        self.assertEqual(material['components']['inner_tank_jersey'], {'cotton': 100})
        self.assertEqual(material['components']['inner_tank_woven'], {'polyester': 65, 'cotton': 35})
        self.assertEqual(self.new_product()['component_compositions'], material)

    def test_314_prior_evidence_and_audits_and_other_brands_are_preserved(self):
        counts = Counter((r['brand_id'], r['month']) for r in self.inventory['entries'][:314])
        for key in ['evidence', 'evidence_audit']:
            groups = []
            for brand in self.coverage['brand_month_coverage']:
                for month, cell in brand['months'].items():
                    count = counts[(brand['brand_id'], month)]
                    if count:
                        groups.append({'brand_id': brand['brand_id'], 'month': month, 'field': key,
                                       'prior_rows': count, 'sha256': digest(cell[key][:count])})
            saved = self.report['preservation'][key + '_prefixes']
            self.assertEqual(sum(r['prior_rows'] for r in groups), saved['rows'])
            self.assertEqual(saved['rows'], 314)
            self.assertEqual(len(groups), saved['groups'])
            self.assertEqual(digest(groups), saved['sha256'])
        others = [b for b in self.coverage['brand_month_coverage'] if b['brand_id'] not in ['BR-00012', 'BR-00013']]
        self.assertEqual(digest(others), self.report['preservation']['unmodified_other_brands_sha256'])

    def test_deferred_months_and_existing_index_june_are_unchanged(self):
        for saved in self.report['preservation']['deferred_or_existing_cells']:
            cell = self.brands[saved['brand_id']]['months'][saved['month']]
            self.assertEqual(cell['status'], saved['status'])
            self.assertEqual(digest(cell), saved['sha256'])
        for brand_id in ['BR-00012', 'BR-00013']:
            for correction in self.report['corrections_appended']:
                if correction['brand_id'] == brand_id:
                    cell = self.brands[brand_id]['months']['2026-03']
                    self.assertTrue(any(e.get('published_date') == '2026-03-19' for e in cell['evidence']))
                    self.assertTrue(correction['old_evidence_and_audit_retained'])

    def test_actual_validator_recounts_cells_observations_without_ledger_promotion(self):
        summary = self.check_coverage()
        self.assertEqual((summary['terminal_brand_month_cells'], summary['verified_product_month_observations']), (68, 84))
        self.assertEqual((summary['partial_brand_month_cells'], summary['not_started_brand_month_cells']), (130, 42))
        self.assertEqual(self.coverage['canonical_record_count'], len(self.ledger['records']))
        self.assertEqual(len(self.ledger['records']), 2)
        self.assertEqual(self.coverage['publication_status'], 'PUBLISH_HOLD')
        self.assertTrue(self.coverage['human_review_required'])
        self.assertEqual(self.coverage['summary']['status'], 'INCOMPLETE')

    def test_article_only_or_missing_women_confirmation_cannot_qualify(self):
        original = copy.deepcopy(self.coverage)
        self.new_product()['source_kind'] = 'OFFICIAL_WORLD_ARTICLE_FIXED_BODY'
        with self.assertRaisesRegex(AssertionError, 'feature-only'):
            self.check_coverage()
        self.coverage = original
        self.brands = {b['brand_id']: b for b in self.coverage['brand_month_coverage']}
        self.new_product()['gender_verified'] = False
        with self.assertRaises(AssertionError):
            self.check_coverage()


if __name__ == '__main__':
    unittest.main()
