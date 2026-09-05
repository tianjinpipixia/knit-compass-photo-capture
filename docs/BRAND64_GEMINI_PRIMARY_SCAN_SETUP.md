# Brand64 Gemini Primary Scan Setup

## Purpose

This is the Phase A execution path for Knit Compass Brand64 daily monitoring.
Gemini performs the first-pass scan of official brand / official EC women's-knit surfaces. ChatGPT Phase B verifies only brands/items surfaced as candidate deltas.

## Files

- `.github/workflows/run-brand64-gemini-primary-scan.yml`
- `scripts/run_brand64_gemini_primary_scan.py`
- output: `data/brand-md-monitoring/gemini-primary-scans/YYYY/MM/brand64_gemini_primary_scan_YYYY-MM-DD.json`
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

## Operational boundaries

- Active brand set comes from `config/brand64-active-brands.json` and must contain exactly 64 active brands.
- Known official URL hints are used for PAL, ZARA and SNIDEL. Other brands may use Gemini Google Search to locate an official brand / official EC women's-knit surface.
- `SOURCE_ACCESS_LIMITED`, `SOURCE_OFFLINE`, `URL_MISSING`, `OFFICIAL_SOURCE_NOT_FOUND`, or a missing Gemini row prevents a complete 64/64 result.
- Missing/inaccessible brands are never interpreted as `difference none`.
- Historical dates without an actual Gemini artifact remain unresolved; the workflow does not fabricate retroactive no-change observations.
- The Gemini surface snapshot is lightweight. It records visible item name, official product URL, displayed price, and visible status labels only.
- Product code, composition, function claims, colors and exact sales/reservation dates belong to ChatGPT Phase B official individual-product verification.
- Sales quantity estimation is forbidden.
- Publication remains `PUBLISH_HOLD` / `HUMAN_REVIEW_REQUIRED`.

## Diff behavior

The runner compares each current `OK` brand surface against the previous comparable Gemini artifact and produces candidate deltas such as:

- `NEW_PRODUCT_CANDIDATE`
- `PRICE_CHANGE_CANDIDATE`
- `SALE_STATUS_CHANGE_CANDIDATE`
- `RESERVATION_STATUS_CHANGE_CANDIDATE`
- `LISTING_STATUS_CHANGE_CANDIDATE`
- `LISTING_PRESENCE_CHANGE_CANDIDATE`

A listing-presence change is only a Phase B verification candidate; absence from one listing surface is not treated as deletion or `SOURCE_OFFLINE`.

## Failure behavior

If `GEMINI_API_KEY` is missing, the runner writes a `GEMINI_SCAN_MISSING` artifact and exits non-zero.
If any brand is missing or source-limited, the runner writes `GEMINI_SCAN_INCOMPLETE` and exits non-zero.
The GitHub Action still uploads and commits the status artifact, then fails visibly so the date cannot be mistaken for a completed no-change day.
