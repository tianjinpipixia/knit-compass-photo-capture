# Brand64 Gemini Primary Scan Setup

## Purpose

This is the Phase A execution path for Knit Compass Brand64 daily monitoring.
The Brand64 universe remains **64 active brands**, while Gemini daily completion requires **39 officially confirmed brands**. ChatGPT Phase B verifies only brands/items surfaced as candidate deltas from those confirmed Gemini scans.

## Files

- `.github/workflows/run-brand64-gemini-primary-scan.yml`
- `scripts/run_brand64_gemini_primary_scan.py`
- `scripts/run_brand64_gemini_primary_scan_39.py`
- output: `data/brand-md-monitoring/gemini-primary-scans/YYYY/MM/brand64_gemini_primary_scan_YYYY-MM-DD_*.json`
- pointer: `data/brand-md-monitoring/gemini-primary-scans/latest.json`

## Required repository secret

Add one GitHub Actions repository secret:

- name: `GEMINI_API_KEY`
- value: Gemini API key created in Google AI Studio

GitHub path:

`Settings` → `Secrets and variables` → `Actions` → `New repository secret`

Do not commit the API key to source control.

## Schedule

The workflow runs daily at 05:30 Asia/Tokyo (20:30 UTC on the previous UTC day).
This is intended to complete before the ChatGPT Brand64 daily verification task.

## 39-brand completion rule

- Active Brand64 master remains exactly 64 brands.
- Gemini Phase A requires **39 brands with `scan_status=OK`** to complete the daily primary scan.
- Priority brands are attempted first: PAL 10 brands, ZARA, SNIDEL, GLOBAL WORK, NATURAL BEAUTY BASIC, VIS, and ROPÉ PICNIC.
- If an attempted brand is source-limited, Gemini continues through the remaining active set until 39 `OK` brands are accumulated or the 64-brand universe is exhausted.
- Once 39 `OK` brands are reached, remaining unneeded brands are stored as `GEMINI_NOT_REQUIRED_TODAY`.
- `GEMINI_NOT_REQUIRED_TODAY` is **not** equivalent to `difference none` and cannot be used as a no-change fact.
- Attempted source-limited brands remain explicitly unresolved even when the daily 39-brand quota is achieved.

## Operational boundaries

- Known official URL hints are used for PAL, ZARA and SNIDEL. Other brands may use Gemini Google Search to locate an official brand / official EC women's-knit surface.
- Missing/inaccessible brands are never interpreted as `difference none`.
- Historical dates without an actual Gemini artifact remain unresolved; the workflow does not fabricate retroactive no-change observations.
- The Gemini surface snapshot is lightweight. It records visible item name, official product URL, displayed price, and visible status labels only.
- Product code, composition, function claims, colors and exact sales/reservation dates belong to ChatGPT Phase B official individual-product verification.
- Sales quantity estimation is forbidden.
- Publication remains `PUBLISH_HOLD` / `HUMAN_REVIEW_REQUIRED`.

## Diff behavior

For each `OK` brand that has a comparable previous Gemini snapshot, the runner may produce candidates such as:

- `NEW_PRODUCT_CANDIDATE`
- `PRICE_CHANGE_CANDIDATE`
- `SALE_STATUS_CHANGE_CANDIDATE`
- `RESERVATION_STATUS_CHANGE_CANDIDATE`
- `LISTING_STATUS_CHANGE_CANDIDATE`
- `LISTING_PRESENCE_CHANGE_CANDIDATE`

A listing-presence change is only a Phase B verification candidate; absence from one listing surface is not treated as deletion or `SOURCE_OFFLINE`.

## Failure behavior

If `GEMINI_API_KEY` is missing, the runner writes a `GEMINI_SCAN_MISSING` artifact and exits non-zero.
If fewer than 39 brands reach `scan_status=OK`, the runner writes `GEMINI_SCAN_INCOMPLETE` and exits non-zero.
If 39 brands reach `OK`, Gemini Phase A is successful even when some additional attempted brands are source-limited; those limited brands remain unresolved and are not treated as no-change.
The GitHub Action uploads and preserves the status artifact so the daily state remains auditable.
