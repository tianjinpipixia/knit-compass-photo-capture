import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def test_spring_backfill_is_independent_and_month_complete_gated():
    cfg = load("config/brand64-md-monitoring.json")
    retro = cfg["retrospective_season_backfill"]
    assert retro["status"] == "INDEPENDENT_BACKFILL_REQUIRED"
    assert retro["retrospective_period"] == "2026-01-01/2026-06-30"
    assert retro["completion_gate"]["complete_only_when_all_brand_months_terminal"] is True
    assert retro["completion_gate"]["source_access_limited_is_not_no_change"] is True
    assert retro["completion_gate"]["season_label_only_does_not_prove_month"] is True

def test_spring_coverage_cannot_claim_complete_while_pending():
    coverage = load("data/brand-md-monitoring/2026-spring-backfill-coverage.json")
    assert coverage["approved_brand_count"] == 40
    assert coverage["summary"]["total_brand_month_cells"] == 240
    config = load("config/brand64-md-monitoring.json")
    terminal = set(config["retrospective_season_backfill"]["completion_gate"]["terminal_month_statuses"])
    completed = sum(all(cell["status"] in terminal for cell in brand["months"].values())
                    for brand in coverage["brand_month_coverage"])
    assert coverage["summary"]["fully_completed_brands"] == completed
    assert coverage["summary"]["status"] == "INCOMPLETE"
    assert coverage["correction"]["previously_reported_retrospective_count_422"] == "NOT_SUPPORTED_BY_CANONICAL_LEDGER"

def test_canonical_ledger_count_is_not_legacy_candidate_count():
    coverage = load("data/brand-md-monitoring/2026-spring-backfill-coverage.json")
    ledger = load("data/brand-md-monitoring/2026-spring-retrospective-baselines.json")
    assert coverage["canonical_record_count"] == len(ledger.get("records", []))
    assert coverage["canonical_record_count"] == 2
