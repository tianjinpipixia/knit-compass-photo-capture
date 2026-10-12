import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_spring_backfill_coverage import evidence_digest, validate


class CoverageIntegrityTests(unittest.TestCase):
    def setUp(self):
        def read(path):
            return json.loads((ROOT / path).read_text(encoding='utf-8'))
        self.coverage = read('data/brand-md-monitoring/2026-spring-backfill-coverage.json')
        self.config = read('config/brand64-md-monitoring.json')
        self.ledger = read(self.config['retrospective_season_backfill']['ledger_path'])
        policy = self.config['retrospective_season_backfill']
        self.references = dict(approved_roster=read(policy['approved_roster_path']),
                               evidence_inventory=read(policy['evidence_inventory_path']),
                               original_audit=read(policy['original_integrity_audit_path']))
        self.references['previous_coverage'] = copy.deepcopy(self.coverage)

    def run_validation(self):
        return validate(self.coverage, self.config, self.ledger, **self.references)

    def cell(self, brand, month):
        return next(b for b in self.coverage['brand_month_coverage'] if b['brand_id'] == brand)['months'][month]

    def test_corrected_repository_data(self):
        result = self.run_validation()
        self.assertEqual(result['total_brand_month_cells'],
                         result['terminal_brand_month_cells'] + result['pending_brand_month_cells'])
        self.assertEqual(result['by_month'], self.coverage['summary']['by_month'])

    def test_all_confirmed_products_from_rechecked_sources_are_registered(self):
        report = json.loads((ROOT / 'data/brand-md-monitoring/2026-10-12-spring-qualifying-source-recheck.json').read_text())
        for finding in report['findings']:
            if finding['status'] != 'VERIFIED_PRODUCTS':
                continue
            expected = {p['product_code'] for p in finding['products']}
            actual = {p['product_code'] for p in self.cell(finding['brand_id'], finding['month'])['verified_product_evidence']}
            self.assertTrue(expected <= actual, f"confirmed source items omitted: {finding['brand_id']} {finding['month']}")

    def test_feature_only_cannot_close_month(self):
        self.cell('BR-00035', '2026-01')['status'] = 'VERIFIED_PRODUCTS'
        with self.assertRaisesRegex(AssertionError, 'terminal product cell'):
            self.run_validation()

    def test_duplicate_feature_url_does_not_inflate_pages(self):
        cell = self.cell('BR-00035', '2026-01')
        cell['official_pages_checked'] += 1
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
            validate(self.coverage, self.config, self.ledger, **self.references,
                     now=datetime(2100, 1, 1, tzinfo=timezone.utc))

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


    def test_partial_cannot_be_promoted_by_config(self):
        self.config['retrospective_season_backfill']['completion_gate']['terminal_month_statuses'].append('PARTIAL')
        with self.assertRaisesRegex(AssertionError, 'status policy'):
            self.run_validation()

    def test_pending_cannot_be_promoted_by_config(self):
        self.config['retrospective_season_backfill']['completion_gate']['terminal_month_statuses'].append('PENDING')
        with self.assertRaisesRegex(AssertionError, 'status policy'):
            self.run_validation()

    def test_same_size_unapproved_roster_rejected(self):
        self.coverage['brand_month_coverage'][0]['brand_id'] = 'BR-99999'
        with self.assertRaisesRegex(AssertionError, 'approved roster'):
            self.run_validation()

    def test_approved_brand_name_cannot_be_replaced(self):
        self.coverage['brand_month_coverage'][0]['brand_name'] = 'Unapproved name'
        with self.assertRaisesRegex(AssertionError, 'approved roster'):
            self.run_validation()

    def test_approved_research_tier_cannot_be_changed(self):
        self.coverage['brand_month_coverage'][0]['research_tier'] = 'MONITORING'
        with self.assertRaisesRegex(AssertionError, 'approved roster'):
            self.run_validation()

    def test_evidence_deletion_with_matching_recount_is_rejected(self):
        cell = self.cell('BR-00035', '2026-05')
        cell['evidence'].clear()
        cell['official_pages_checked'] = 0
        with self.assertRaisesRegex(AssertionError, 'preserved evidence'):
            self.run_validation()

    def test_deletion_of_duplicate_url_observation_is_rejected(self):
        cell = self.cell('BR-00035', '2026-01')
        cell['evidence'].pop()
        cell['evidence_audit'].pop()
        with self.assertRaisesRegex(AssertionError, 'preserved evidence'):
            self.run_validation()

    def test_observed_fact_rewrite_is_rejected(self):
        self.cell('BR-00035', '2026-01')['evidence'][0]['observed_fact'] = 'replacement'
        with self.assertRaisesRegex(AssertionError, 'preserved evidence'):
            self.run_validation()

    def test_audit_deletion_is_rejected(self):
        self.cell('BR-00035', '2026-01')['evidence_audit'].pop()
        with self.assertRaisesRegex(AssertionError, 'evidence/audit row count'):
            self.run_validation()

    def test_audit_source_change_is_rejected(self):
        self.cell('BR-00035', '2026-01')['evidence_audit'][0]['url'] = 'https://example.com/other'
        with self.assertRaisesRegex(AssertionError, 'evidence/audit source'):
            self.run_validation()

    def test_new_evidence_can_be_appended(self):
        cell = self.cell('BR-00035', '2026-01')
        row = copy.deepcopy(cell['evidence'][0])
        row['observed_fact'] = 'Unit test supplementary observation; no qualification claimed.'
        cell['evidence'].append(row)
        audit = copy.deepcopy(cell['evidence_audit'][0])
        audit['evidence_index'] = len(cell['evidence']) - 1
        cell['evidence_audit'].append(audit)
        inventory = self.references['evidence_inventory']
        with self.assertRaisesRegex(AssertionError, 'registered in the preservation inventory'):
            self.run_validation()
        inventory['entries'].append({'brand_id': 'BR-00035', 'month': '2026-01',
                                     'evidence_sha256': evidence_digest(row)})
        inventory['evidence_rows'] += 1
        self.run_validation()
        self.references['previous_coverage'] = copy.deepcopy(self.coverage)
        cell['evidence'].pop()
        cell['evidence_audit'].pop()
        inventory['entries'].pop()
        inventory['evidence_rows'] -= 1
        with self.assertRaisesRegex(AssertionError, 'previous-commit evidence'):
            self.run_validation()

    def test_coverage_and_approved_roster_cannot_be_replaced_together(self):
        self.coverage['brand_month_coverage'][0]['brand_id'] = 'BR-99999'
        self.references['approved_roster']['records'][0]['brand_id'] = 'BR-99999'
        with self.assertRaisesRegex(AssertionError, 'owner-approved scope'):
            self.run_validation()

    def test_roster_provenance_cannot_be_changed(self):
        self.references['approved_roster']['source_blob_sha'] = '0' * 40
        with self.assertRaisesRegex(AssertionError, 'source blob mismatch'):
            self.run_validation()

    def test_coverage_and_initial_inventory_cannot_be_deleted_together(self):
        cell = self.cell('BR-00035', '2026-01')
        row = cell['evidence'].pop(1)
        cell['evidence_audit'].pop(1)
        inventory = self.references['evidence_inventory']
        entry = next(e for e in inventory['entries'] if e['brand_id'] == 'BR-00035'
                     and e['month'] == '2026-01' and e['evidence_sha256'] == evidence_digest(row))
        inventory['entries'].remove(entry)
        inventory['evidence_rows'] -= 1
        with self.assertRaisesRegex(AssertionError, 'initial evidence inventory'):
            self.run_validation()

    def test_cli_reads_previous_commit_even_when_current_inventory_is_recounted(self):
        policy = self.config['retrospective_season_backfill']
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                'config/brand64-md-monitoring.json': self.config,
                policy['coverage_status_path']: self.coverage,
                policy['ledger_path']: self.ledger,
                policy['approved_roster_path']: self.references['approved_roster'],
                policy['evidence_inventory_path']: self.references['evidence_inventory'],
                policy['original_integrity_audit_path']: self.references['original_audit'],
            }
            for path, data in files.items():
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(json.dumps(data, ensure_ascii=False))
            previous = copy.deepcopy(self.coverage)
            row = copy.deepcopy(self.cell('BR-00035', '2026-01')['evidence'][0])
            row['observed_fact'] = 'Synthetic previously committed observation.'
            brand = next(b for b in previous['brand_month_coverage'] if b['brand_id'] == 'BR-00035')
            cell = brand['months']['2026-01']
            cell['evidence'].append(row)
            audit = copy.deepcopy(cell['evidence_audit'][0])
            audit['evidence_index'] = len(cell['evidence']) - 1
            cell['evidence_audit'].append(audit)
            inventory = copy.deepcopy(self.references['evidence_inventory'])
            inventory['entries'].append({'brand_id': 'BR-00035', 'month': '2026-01',
                                         'evidence_sha256': evidence_digest(row)})
            inventory['evidence_rows'] += 1
            (root / policy['coverage_status_path']).write_text(json.dumps(previous))
            (root / policy['evidence_inventory_path']).write_text(json.dumps(inventory))
            def git(*args):
                return subprocess.run(['git', *args], cwd=root, check=True,
                                      capture_output=True, text=True).stdout.strip()
            git('init', '-q')
            git('add', policy['coverage_status_path'], policy['evidence_inventory_path'])
            git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                '-c', 'commit.gpgsign=false', 'commit', '-qm', 'Synthetic valid append baseline')
            commit = git('rev-parse', 'HEAD')
            command = [sys.executable, str(ROOT / 'scripts/validate_spring_backfill_coverage.py'),
                       '--root', str(root), '--previous-ref', commit]
            positive = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(positive.returncode, 0, positive.stderr)
            self.assertEqual(json.loads(positive.stdout)['history_preservation'], 'PREVIOUS_COMMIT_CHECKED')
            (root / policy['coverage_status_path']).write_text(json.dumps(self.coverage))
            (root / policy['evidence_inventory_path']).write_text(json.dumps(self.references['evidence_inventory']))
            negative = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(negative.returncode, 0)
            self.assertIn('previous-commit evidence deleted or rewritten', negative.stderr)

    def test_truthy_no_products_claims_are_rejected(self):
        cell = self.cell('BR-00035', '2026-01')
        cell['status'] = 'VERIFIED_NO_PRODUCTS'
        cell['last_checked_at'] = '2026-10-12T01:00:00Z'
        cell['unresolved_reason'] = None
        for evidence in ('claim', [{}]):
            with self.subTest(evidence=evidence):
                cell['no_products_evidence'] = evidence
                with self.assertRaisesRegex(AssertionError, 'no-products'):
                    self.run_validation()


if __name__ == '__main__':
    unittest.main()

