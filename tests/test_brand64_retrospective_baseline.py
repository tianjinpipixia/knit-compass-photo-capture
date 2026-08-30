from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from brand64_retrospective_baseline import SUMMARY_START, execute  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


class RetrospectiveBaselineTest(unittest.TestCase):
    def fixture(self, *, gaps: list[str] | None = None) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        active = {"BR-00001": "GLOBAL WORK", "BR-00002": "VIS"}
        write_json(root / "config/brand64-active-brands.json", {"active_brands": active})
        write_json(root / "config/brand64-md-monitoring.json", {
            "retrospective_season_backfill": {
                "retrospective_period": "2026-01-01/2026-04-30",
                "execution_order": [
                    "CURRENT_DAY_BRAND64_COMPLETE",
                    "UNPROCESSED_OBSERVATION_DATES_RECOVERED",
                    "RETROSPECTIVE_BASELINE",
                ],
                "readiness": {
                    "latest_observed_date_must_equal_run_date": True,
                    "required_light_check_count": 2,
                    "required_checked_brand_count": 2,
                    "observation_gap_dates_must_be_empty": True,
                },
                "priority_brand_ids": ["BR-00001", "BR-00002"],
                "max_products_per_run": 3,
                "max_products_per_brand_per_run": 2,
                "accepted_source_kinds": ["OFFICIAL_PRODUCT_PAGE"],
                "ledger_path": "data/brand-md-monitoring/2026-spring-retrospective-baselines.json",
                "report_path_pattern": "data/brand-md-monitoring/{observed_date}-retrospective-season-backfill-report.json",
            }
        })
        daily_path = "data/brand-md-monitoring/2026-08-30-brand64-daily.json"
        summary_path = "data/brand-md-monitoring/2026-08-30-brand64-summary.md"
        write_json(root / "data/brand-md-monitoring/latest.json", {
            "observed_date": "2026-08-30",
            "daily_path": daily_path,
            "summary_path": summary_path,
            "observation_gap_dates": gaps or [],
        })
        write_json(root / daily_path, {
            "observed_date": "2026-08-30",
            "light_check_count": 2,
            "checked_brand_ids": list(active),
            "observation_gap_dates": gaps or [],
            "current_first_seen_product_count": 0,
            "retrospective_backfill_product_count": 0,
        })
        (root / summary_path).write_text("# Daily\n", encoding="utf-8")
        write_json(root / "data/brand-md-monitoring/2026-spring-retrospective-baselines.json", {
            "format": "KC_BRAND64_RETROSPECTIVE_BASELINE_LEDGER",
            "schema_version": "1.0",
            "retrospective_period": "2026-01-01/2026-04-30",
            "record_scope": "RETROSPECTIVE_BASELINE",
            "records": [],
            "metrics": {"retrospective_season_backfill_cumulative_count": 0, "counts_by_brand": {}},
        })
        (root / "data/brand-md-monitoring/2026-08-29-product-baseline-snapshots.jsonl").write_text(
            json.dumps({
                "product_code": "EXISTING-1",
                "official_url": "https://official.example/products/existing-1",
            }) + "\n",
            encoding="utf-8",
        )
        return root

    @staticmethod
    def candidate(brand_id: str, brand_name: str, code: str) -> dict:
        return {
            "record_scope": "RETROSPECTIVE_BASELINE",
            "retrospective_period": "2026-01-01/2026-04-30",
            "brand_id": brand_id,
            "brand_name": brand_name,
            "product_name": f"Spring knit {code}",
            "product_code": code,
            "regular_price_jpy": None,
            "sale_price_jpy": None,
            "composition": None,
            "function_claims": None,
            "colors": None,
            "launch_status": None,
            "official_url": f"https://official.example/products/{code.lower()}",
            "source_kind": "OFFICIAL_PRODUCT_PAGE",
            "source_status": "ONLINE",
            "period_evidence": {"kind": "OFFICIAL_RELEASE_DATE", "value": "2026-03-15"},
            "confirmed_at": "2026-08-30T09:00:00+09:00",
            "last_checked_at": "2026-08-30T09:00:00+09:00",
            "sales_quantity": "NOT_AVAILABLE",
            "publication_status": "PUBLISH_HOLD",
            "human_review_required": True,
        }

    def test_gate_skips_when_an_unprocessed_date_remains(self) -> None:
        root = self.fixture(gaps=["2026-08-29"])
        report = execute(root, run_date="2026-08-30", apply=True)
        self.assertEqual(report["status"], "SKIPPED")
        self.assertIn("UNPROCESSED_OBSERVATION_DATES_REMAIN", report["gate_reasons"])
        ledger = json.loads((root / "data/brand-md-monitoring/2026-spring-retrospective-baselines.json").read_text())
        self.assertEqual(ledger["records"], [])

    def test_zero_new_products_keeps_the_advanced_latest_date(self) -> None:
        root = self.fixture()
        report = execute(root, run_date="2026-08-30", apply=True, strict=True)
        latest = json.loads((root / "data/brand-md-monitoring/latest.json").read_text())
        self.assertEqual(latest["observed_date"], "2026-08-30")
        self.assertEqual(latest["retrospective_season_backfill_count"], 0)
        self.assertEqual(report["retrospective_season_backfill_count"], 0)

    def test_ingest_uses_official_pages_dedupes_and_recounts_actual_rows(self) -> None:
        root = self.fixture()
        candidates = [
            self.candidate("BR-00001", "GLOBAL WORK", "GW-001"),
            self.candidate("BR-00001", "GLOBAL WORK", "GW-001"),
            self.candidate("BR-00001", "GLOBAL WORK", "EXISTING-1"),
            self.candidate("BR-00002", "VIS", "VIS-001"),
        ]
        candidates[2]["official_url"] = "https://official.example/products/existing-1?tracking=1"
        input_path = root / "verified-input.json"
        write_json(input_path, candidates)

        report = execute(root, run_date="2026-08-30", input_path=input_path, apply=True, strict=True)
        self.assertEqual(report["accepted_count"], 2)
        self.assertEqual(report["duplicate_input_count"], 1)
        self.assertEqual(report["duplicate_existing_count"], 1)
        self.assertEqual(report["retrospective_season_backfill_count"], 2)
        self.assertEqual(report["retrospective_season_backfill_cumulative_count"], 2)

        latest = json.loads((root / "data/brand-md-monitoring/latest.json").read_text())
        daily = json.loads((root / latest["daily_path"]).read_text())
        ledger = json.loads((root / latest["retrospective_season_backfill_path"]).read_text())
        summary = (root / latest["summary_path"]).read_text()
        self.assertEqual(latest["retrospective_season_backfill_count"], 2)
        self.assertEqual(daily["retrospective_season_backfill_count"], 2)
        self.assertEqual(len(ledger["records"]), 2)
        self.assertTrue(all(row["product_id"].startswith("B64_RETRO_") for row in ledger["records"]))
        self.assertTrue(all(row["product_url"] == row["official_url"] for row in ledger["records"]))
        self.assertTrue(all(row["record_scope"] == "RETROSPECTIVE_BASELINE" for row in ledger["records"]))
        self.assertIn(SUMMARY_START, summary)
        self.assertTrue(all(row["publication_status"] == "PUBLISH_HOLD" for row in ledger["records"]))
        self.assertTrue(all(row["human_review_required"] for row in ledger["records"]))

        rerun = execute(root, run_date="2026-08-30", input_path=input_path, apply=True, strict=True)
        self.assertEqual(rerun["accepted_count"], 0)
        self.assertEqual(rerun["updated_count"], 2)
        self.assertEqual(rerun["retrospective_season_backfill_count"], 2)
        ledger_after = json.loads((root / latest["retrospective_season_backfill_path"]).read_text())
        self.assertEqual(len(ledger_after["records"]), 2)

    def test_rejects_category_sources_and_estimated_sales(self) -> None:
        root = self.fixture()
        candidate = self.candidate("BR-00001", "GLOBAL WORK", "GW-002")
        candidate["source_kind"] = "OFFICIAL_CATEGORY_PAGE"
        candidate["sales_quantity"] = 100
        input_path = root / "invalid-input.json"
        write_json(input_path, [candidate])
        with self.assertRaises(ValueError):
            execute(root, run_date="2026-08-30", input_path=input_path, apply=True, strict=True)


if __name__ == "__main__":
    unittest.main()
