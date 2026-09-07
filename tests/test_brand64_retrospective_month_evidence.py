import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
import merge_brand64_retrospective_sources as retro


class RetrospectiveMonthEvidenceTests(unittest.TestCase):
    def test_explicit_product_month_does_not_become_verification_month(self):
        row = retro.normalize_record({
            'brand_id': 'BR-1',
            'brand_name': 'Example',
            'product_name': 'April knit',
            'product_url': 'https://example.com/products/1',
            'verification_date': '2026-09-08',
            'snapshot_date': '2026-09-08',
            'retrospective_months': ['2026-04'],
            'period_evidence_kind': 'OFFICIAL_PREORDER_DELIVERY_MONTH',
            'period_evidence_value': '2026年4月中旬頃',
            'eligible_for_cumulative': True,
        }, 'manual-apr.json', manual=True)
        self.assertEqual(row['retrospective_months'], ['2026-04'])
        self.assertEqual(row['verification_date'], '2026-09-08')
        self.assertEqual(row['period_evidence_kind'], 'OFFICIAL_PREORDER_DELIVERY_MONTH')
        self.assertNotIn('2026-09', row['retrospective_months'])

    def test_all_manual_batch_files_are_collected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = pathlib.Path(tmp)
            manual_dir = repo/'data/brand-md-monitoring/retrospective'
            manual_dir.mkdir(parents=True)
            (manual_dir/'manual-products.json').write_text(json.dumps({'records': [
                {'brand_id':'BR-1','product_url':'https://example.com/a'}
            ]}))
            (manual_dir/'manual-apr-jun.json').write_text(json.dumps({'records': [
                {'brand_id':'BR-1','product_url':'https://example.com/b'}
            ]}))
            sources = retro.collect_sources(repo)
            urls = {source[0]['product_url'] for source in sources}
            self.assertEqual(urls, {'https://example.com/a', 'https://example.com/b'})


if __name__ == '__main__':
    unittest.main()
