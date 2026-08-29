#!/usr/bin/env python3
"""Validate Issue #87 month-scoped product-selection contract and GLOBAL WORK fixture."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config/proposal-workspace-month-scope-contract.json"
FIXTURE = ROOT / "data/brand-md-monitoring/2026-08-20-global-work-month-scope-fixture.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    contract = load(CONTRACT)
    fixture = load(FIXTURE)

    assert contract.get("format") == "KC_PROPOSAL_WORKSPACE_MONTH_SCOPE_CONTRACT"
    assert contract.get("issue") == 87
    assert contract.get("target_route") == "/proposal-workspace#product"

    source_boundary = contract.get("source_boundary", {})
    assert source_boundary.get("chatgpt_sites_latest_source_is_canonical_for_public_ui") is True
    assert source_boundary.get("do_not_overwrite_sites_with_older_github_or_drive_snapshot") is True

    scope = contract.get("selection_scope", {})
    assert scope.get("keys") == ["brand_id", "fiscal_year", "selected_month"]
    assert scope.get("product_list_must_recompute_on_any_scope_change") is True
    assert scope.get("keep_previous_month_products_in_normal_list") is False
    assert scope.get("auto_select_first_product") is False
    assert scope.get("empty_month_uses_previous_products_as_fallback") is False

    month = contract.get("month_resolution", {})
    assert month.get("preorder_counts_as_primary_entry_when_first_commercial_event") is True
    assert month.get("sales_start_is_primary_when_no_prior_confirmed_preorder") is True
    assert month.get("first_seen_is_not_launch_month") is True
    assert month.get("delivery_month_is_not_new_launch_month") is True
    assert month.get("unknown_month_bucket") == "MONTH_UNRESOLVED"

    carryover = contract.get("carryover_policy", {})
    assert carryover.get("requires_explicit_evidence") is True
    assert carryover.get("previous_month_presence_is_not_carryover_evidence") is True
    assert carryover.get("include_in_new_launch_count") is False

    special = contract.get("special_policy", {})
    assert special.get("keep_record") is True
    assert special.get("include_in_mainline_style_count") is False
    assert special.get("include_in_main_material_aggregation") is False
    assert special.get("display_separately") is True

    reset = contract.get("reset_contract", {})
    assert set(reset.get("triggers", [])) == {"brand_change", "fiscal_year_change", "month_change"}
    required_state = {
        "selectedProductId",
        "selectedProduct",
        "selectedMaterialCandidateId",
        "selectedMaterialCandidate",
        "selectedKnitCandidateId",
        "selectedKnitCandidate",
        "selectedDesignProposalId",
        "selectedDesignProposal",
    }
    assert required_state <= set(reset.get("clear_state_keys", []))
    assert reset.get("delete_underlying_product_records") is False
    assert reset.get("auto_restore_previous_selection_when_returning_to_month") is False

    downstream = contract.get("downstream_gate", {})
    assert downstream.get("material_step_requires_current_scope_product") is True
    assert downstream.get("knit_step_requires_current_scope_product") is True
    assert downstream.get("design_step_requires_current_scope_product") is True
    assert downstream.get("stale_product_must_not_feed_downstream") is True

    empty = contract.get("empty_state", {})
    assert empty.get("show_previous_month_products") is False
    assert empty.get("show_unresolved_products_inline") is False

    safety = contract.get("safety_boundaries", {})
    assert safety.get("human_review") == "UNCHANGED"
    assert safety.get("pending") == "UNCHANGED"
    assert safety.get("not_promoted") == "UNCHANGED"
    assert safety.get("publish_hold") == "UNCHANGED"
    assert safety.get("sales_quantity_estimation") == "FORBIDDEN"

    assert fixture.get("brand_id") == "BR-00006"
    assert fixture.get("brand_name") == "GLOBAL WORK"
    assert fixture.get("fiscal_year") == 2026

    products = {row["product_code"]: row for row in fixture.get("products", [])}
    expected_mainline_august = {"826491", "1051672", "1051195", "670330"}
    assert expected_mainline_august <= set(products)
    for code in expected_mainline_august:
        row = products[code]
        assert row.get("bucket") == "MAINLINE"
        assert row.get("md_primary_month") == "2026-08"

    # Reservation in August with September delivery remains an August primary MD event only.
    for code in {"826491", "670330"}:
        row = products[code]
        assert row.get("preorder_start_date", "").startswith("2026-08")
        assert row.get("delivery_expected_month") == "2026-09"
        assert row.get("md_primary_month") == "2026-08"
        assert row.get("count_as_new_in_delivery_month") is False

    assert products["670330"].get("composition") == "Acrylic 48% / Cotton 37% / Polyester 15%"
    assert products["670330"].get("knit_structure_status") == "OWNER_INFERENCE_NOT_YET_CONFIRMED"
    assert products["1051672"].get("weight_g_approx") == 280
    assert products["1051195"].get("weight_g_approx") == 400

    # STAFF LAB stays visible as a reference but cannot pollute mainline counts/material aggregation.
    staff = products["1044391"]
    assert staff.get("bucket") == "SPECIAL_TEST"
    assert staff.get("special_program") == "STAFF LAB"
    assert staff.get("include_in_mainline_style_count") is False
    assert staff.get("include_in_main_material_aggregation") is False

    # GU competitor is a relationship only, never a GLOBAL WORK product row.
    competitors = fixture.get("competitor_references", [])
    gu = next(row for row in competitors if row.get("product_code") == "360801")
    assert gu.get("brand_id") == "BR-00002"
    assert gu.get("knit_structure") == "WJQD"
    assert gu.get("include_in_global_work_product_count") is False

    print(
        "proposal workspace month scope: OK "
        "(strict brand/year/month filter, no stale selection, no auto-select, August preorder not double-counted in September, STAFF LAB separated)"
    )


if __name__ == "__main__":
    main()
