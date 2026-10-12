import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from validate_brand64_daily_freshness import validate_archived_period, validate_retrospective_policy


class PolicyCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'config/brand64-md-monitoring.json').read_text())
        self.active = json.loads((ROOT / 'config/brand64-active-brands.json').read_text())['active_brands']

    def test_current_approved_independent_policy(self):
        self.assertEqual(validate_retrospective_policy(self.config, self.active)['retrospective_period'], '2026-01-01/2026-06-30')

    def test_old_daily_capacity_gate_is_rejected(self):
        self.config['retrospective_season_backfill']['status'] = 'ENABLED_WHEN_DAILY_CAPACITY_REMAINS'
        with self.assertRaises(AssertionError):
            validate_retrospective_policy(self.config, self.active)

    def test_feature_pages_cannot_become_accepted_sources(self):
        self.config['retrospective_season_backfill']['accepted_source_kinds'].append('OFFICIAL_FEATURE_PAGE')
        with self.assertRaises(AssertionError):
            validate_retrospective_policy(self.config, self.active)

    def test_review_hold_cannot_be_relaxed(self):
        self.config['retrospective_season_backfill']['human_review_required'] = False
        with self.assertRaises(AssertionError):
            validate_retrospective_policy(self.config, self.active)

    def test_access_limits_cannot_be_treated_as_no_change(self):
        self.config['retrospective_season_backfill']['completion_gate']['source_access_limited_is_not_no_change'] = False
        with self.assertRaises(AssertionError):
            validate_retrospective_policy(self.config, self.active)

    def test_original_archived_scope_is_preserved(self):
        self.assertEqual(validate_archived_period('2026-01-01/2026-04-30', '2026-01-01/2026-06-30'), '2026-01-01/2026-04-30')

    def test_archive_cannot_extend_outside_approved_scope(self):
        with self.assertRaises(AssertionError):
            validate_archived_period('2026-01-01/2026-07-31', '2026-01-01/2026-06-30')

    def test_reversed_archive_period_is_rejected(self):
        with self.assertRaises(AssertionError):
            validate_archived_period('2026-04-30/2026-01-01', '2026-01-01/2026-06-30')


if __name__ == '__main__':
    unittest.main()
