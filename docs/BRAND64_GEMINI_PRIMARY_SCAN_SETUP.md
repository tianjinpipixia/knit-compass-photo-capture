# Brand64 Gemini Primary Scan Setup

## Purpose

Knit Compass Brand64 uses a two-stage Phase A so the daily operation can stay inside the Gemini free tier while still preserving official-source evidence and Gemini's role in MD review.

1. **Direct official-site collector** (05:30 JST): fetches configured official brand / official EC pages with no paid AI/search API, preserves product observations and unresolved gaps.
2. **Gemini MD pass** (05:50 JST): Gemini inspects supplied official URLs with **URL Context only**, using the direct official-source snapshot as supporting evidence. Google Search grounding is disabled.

The Brand64 universe remains **64 active brands**. Gemini daily completion requires **39 officially confirmed brands (`scan_status=OK`)**.

## Files

Direct collection:
- `.github/workflows/run-brand64-gemini-primary-scan.yml` (historical filename; now the free direct collector)
- `scripts/run_brand64_free_direct_scan.py`
- `scripts/brand64_flash_pipeline.py`
- `config/brand64-free-direct-sources.json`
- state/feed: `data/brand-md-monitoring/direct-scans/` and branch `brand64/flash-feed`

Gemini free-tier MD pass:
- `.github/workflows/run-brand64-gemini-md-free-tier.yml`
- `scripts/run_brand64_gemini_md_free_tier.py`
- `tests/test_brand64_gemini_md_free_tier.py`
- output: `data/brand-md-monitoring/gemini-md/YYYY-MM-DD/gemini-md-*.json`
- pointer: `data/brand-md-monitoring/gemini-md/latest.json`

## Required repository secret

- `GEMINI_API_KEY` — Gemini API key created in Google AI Studio.

Optional repository variable:
- `GEMINI_MD_MODEL` — defaults to stable `gemini-2.5-flash-lite`.

Do not commit API keys to source control.

## Free-tier quota strategy

The previous implementation could keep sending requests after HTTP 429 and also used Google Search grounding. The new Gemini pass is deliberately conservative:

- stable model default: `gemini-2.5-flash-lite`;
- **Google Search grounding disabled**;
- **URL Context only** using known official URLs;
- 13 brands per request (below the URL Context 20-URL request limit);
- up to 5 batches, normally 3 batches are enough for 39 brands if all succeed;
- 65-second spacing between requests;
- on HTTP 429, wait once and retry the same request once;
- if the retry is also 429, abort the Gemini run immediately instead of burning the remaining daily quota;
- the direct collector still preserves official observations even when Gemini is quota-limited.

## 39-brand completion rule

- Active Brand64 master remains exactly 64 brands.
- Priority order starts with PAL 10, ZARA, SNIDEL, GLOBAL WORK, NATURAL BEAUTY BASIC, VIS and ROPÉ PICNIC.
- Then other active brands with strong same-day direct-source evidence are used to fill the 39-brand Gemini target.
- Only Gemini rows with `scan_status=OK` count toward 39.
- Source-limited / offline / not-found brands remain unresolved and are never interpreted as no-change.
- Reaching 39 does not make the unreviewed remainder a no-change fact.

## MD information collected

For `OK` brands Gemini may record current official MD signals such as:
- NEW / PREORDER / SALE / PRICE;
- COLOR / MATERIAL / FUNCTION / DESIGN;
- RESTOCK / SOLD_OUT / RANKING / PROMOTION;
- SEASON / CATEGORY and other useful current official signals.

Gemini output remains `PUBLISH_HOLD` / `HUMAN_REVIEW_REQUIRED`. Product codes, detailed compositions, exact launch dates and other product-level facts still require ChatGPT Phase B verification on official individual product pages when necessary. Sales quantity estimation is forbidden.

## Failure behavior

- Missing API key: `GEMINI_SCAN_MISSING`.
- Fewer than 39 confirmed brands: `GEMINI_SCAN_INCOMPLETE`.
- Repeated HTTP 429: artifact is preserved, then the run aborts without additional Gemini requests.
- Historical dates without actual Gemini artifacts remain unresolved; current live results are never relabeled as historical no-change observations.
