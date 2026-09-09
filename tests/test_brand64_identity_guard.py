import sys, pathlib, unittest, copy, tempfile, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from brand64_identity_guard import reconcile_identities, apply_identity_resolutions
from brand64_canonical_store import read_pool
from publish_brand64_flash_feed import build_cumulative_product_shards

class IdentityGuardTest(unittest.TestCase):
    def test_export_counts_only_valid_identity_and_retains_exact_previous_record(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            row = {'brand_id': 'BR-00069', 'brand_name': 'PROPORTION BODY DRESSING',
                   'product_url': 'https://mix.tokyo/products/1', 'product_name': 'Knit',
                   'scope_status': 'BRAND_AND_KNIT_PATH_MATCHED', 'first_seen_date': '2026-08-03'}
            (root/'known-products.json').write_text(json.dumps({'BR-00069|'+row['product_url']: row}))
            (root/'latest.json').write_text(json.dumps({'observed_date': '2026-09-09'}))
            build_cumulative_product_shards(root)
            previous = next(iter(read_pool(root).values()))
            build_cumulative_product_shards(root, {'BR-00069': 'DOUDOU'})
            manifest = json.loads((root/'cumulative-products/manifest.json').read_text())
            self.assertEqual(manifest['cumulative_unique_product_count'], 0)
            self.assertEqual(manifest['identity_review_product_count'], 1)
            review = json.loads((root/'cumulative-products/review-queue.json').read_text())['records']
            self.assertEqual(review[0]['record'], previous)
            # A fresh import of the same conflicting legacy row remains excluded.
            (root/'known-products.json').write_text(json.dumps({'BR-00069|'+row['product_url']: row}))
            build_cumulative_product_shards(root, {'BR-00069': 'DOUDOU'})
            self.assertEqual(json.loads((root/'cumulative-products/manifest.json').read_text())['cumulative_unique_product_count'], 0)

    def test_collision_is_retained_whole_and_never_relabelled(self):
        row = {'brand_id': 'BR-00069', 'brand_name': 'PROPORTION BODY DRESSING',
               'product_url': 'https://mix.tokyo/products/1216270606', 'history': [{'date': '2026-08-03'}]}
        original = copy.deepcopy(row)
        accepted, review = reconcile_identities({'k': row}, {'BR-00069': 'DOUDOU'}, [])
        self.assertEqual(accepted, {})
        self.assertEqual(review[0]['record'], original)
        self.assertEqual(row, original)
        self.assertEqual(reconcile_identities({'k': row}, {'BR-00069': 'DOUDOU'}, review)[1], review)

    def test_placeholder_resolution_retains_every_prior_field(self):
        row = {'brand_id': 'BR-00058', 'brand_name': 'BR-00058', 'first_seen_date': '2026-07-11', 'detail': {'x': 2}}
        accepted, review = reconcile_identities({'k': row}, {'BR-00058': 'Te chichi'}, [])
        self.assertEqual(accepted['k']['brand_name'], 'Te chichi')
        self.assertEqual(accepted['k']['brand_identity_history'], [row])
        self.assertEqual(accepted['k']['detail'], row['detail'])
        self.assertEqual(review, [])
        self.assertEqual(reconcile_identities(accepted, {'BR-00058': 'Te chichi'}, review)[0], accepted)

    def test_unknown_brand_cannot_enter_counted_pool(self):
        accepted, review = reconcile_identities({'x': {'brand_id': 'unknown', 'brand_name': 'X'}}, {}, [])
        self.assertEqual(accepted, {})
        self.assertEqual(review[0]['reason'], 'BRAND_IDENTITY_CONFLICT')

    def test_evidenced_outside_roster_resolution_keeps_original(self):
        row = {'brand_name': 'Legacy brand', 'product_url': 'https://example.com/1'}
        review = [{'reason': 'BRAND_IDENTITY_CONFLICT', 'identity_key': 'k', 'record': row}]
        decision = {'confirmed_brand_name': 'Legacy brand', 'source_url': row['product_url'], 'verified_at_utc': '2026-09-09T00:00:00Z', 'outcome': 'OUTSIDE_ACTIVE_ROSTER'}
        result = apply_identity_resolutions(review, {}, {'b': 'Active brand'}, {'k': decision})
        self.assertEqual(result[0]['review_status'], 'RESOLVED')
        self.assertEqual(result[0]['record'], row)
        self.assertNotIn('review_status', apply_identity_resolutions(result, {}, {'b': 'Legacy brand'}, {'k': decision})[0])
        self.assertNotIn('review_status', apply_identity_resolutions(result, {}, {}, {})[0])

    def test_duplicate_resolution_requires_matching_canonical_target(self):
        row = {'brand_name': 'Correct brand', 'product_url': 'https://example.com/2'}
        review = [{'reason': 'BRAND_IDENTITY_CONFLICT', 'identity_key': 'old', 'record': row}]
        decision = {'confirmed_brand_name': row['brand_name'], 'source_url': row['product_url'], 'verified_at_utc': '2026-09-09T00:00:00Z', 'outcome': 'ALREADY_CORRECTED_IN_CANONICAL', 'canonical_identity_key': 'new'}
        self.assertNotIn('review_status', apply_identity_resolutions(review, {}, {'b': 'Correct brand'}, {'old': decision})[0])
        known = {'new': dict(row, brand_id='b')}
        self.assertEqual(apply_identity_resolutions(review, known, {'b': 'Correct brand'}, {'old': decision})[0]['review_status'], 'RESOLVED')
        wrong = dict(decision, source_url='https://example.com/other')
        self.assertNotIn('review_status', apply_identity_resolutions(review, known, {'b': 'Correct brand'}, {'old': wrong})[0])
