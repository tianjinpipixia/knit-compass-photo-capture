# Brand64 listing recovery and audit follow-up — 2026-10-07

## Production verification after PR #200

[PR #200](https://github.com/tianjinpipixia/knit-compass-photo-capture/pull/200) was squash-merged as `7da5723c10b3f7982a3c8e11732a6f1ac64dd0fa`.
[Run 37620381937](https://github.com/tianjinpipixia/knit-compass-photo-capture/actions/runs/37620381937) executed the merged code on Ubuntu 26.04.1 / Python 3.12.14 with checkout v5, setup-python v6 and upload-artifact v6.

- All 60 collection regression tests passed on Ubuntu 26.
- Restoration, cumulative publication, flash/retry/detail processing, both artifact uploads, canonical snapshot binding and result-branch preservation succeeded.
- 1,471 observed products across 41 brands; 16 pending pages; zero certified-complete brands. The strict coverage check and final failure guard returned exit 1, as designed.
- DoCLASSE changed from zero live observations to 133 observed products in this bounded production run. It still had a category page pending and the superseded homepage in the saved recovery queue.
- Canonical snapshot: 3,273 products; manifest SHA256 `7e7409a9bb2fa3529b0389b22d24b55b6a2de566e4c1e57af98408f3a00e44ff`.
- Snapshot publication commit: `3ee60f122a17311c0c9b218848ef70e56ea9d1a8`. Flash artifact `11482336075`; final artifact `11481403638`.

This verifies actual collection/preservation on Ubuntu 26 / Node 24. It does not certify complete source coverage or promote candidates for customer publication.

## Follow-up fixes

### 23ku and Kumikyoku

The official 23ku shop navigation identifies brand code `002` and women `gc=2`. Kumikyoku's existing registered listing identifies brand code `003`. Official category navigation identifies knit `scc=1004` and cardigan `scc=1005`.

The old shop entry has no supported cards. The old Kumikyoku all-items response exceeds 4 MB. A ten-card category response still contains approximately 7.5 MB of HTML (diagnostic response: 7,473,105 bytes; SHA256 `02cc1a4354f9c77708643de9187f28513fb4a448e2856c9310784f174fb09d88`). Merely lowering page size cannot fix the transport bound.

Configure two explicit category listings per brand, with `bc=002/003`, `gc=2`, `du=2`, `pp=10`, `scc=1004/1005`. Only those precise routes receive an 8,000,000-byte limit. All other routes retain 4,000,000 bytes. Redirects must satisfy both the requested and final URL's bound; oversized bodies remain errors.

Current HTML renders `c-item-card`, exact visible brand, product name/price/status, and `data-web-tracking-item` with brand code, category code and product ID. The adapter requires matching fields and an official product URL; it rejects other brands, genders, categories, accessories and mismatched IDs. Colour variants deduplicate by product path. Only `c-pagination__next` with an increment of one and unchanged scope filters is followed.

Bounded local verification: 23ku 12 products / four pages / zero errors; Kumikyoku 11 products / four pages / zero errors. Both still have knit and cardigan page 3 queued. These are local samples, not published production counts or exhaustive catalog totals.

### AMERICAN HOLIC

The current brand landing page has no knit product anchors. Its own navigation links to:

- `https://stripe-club.com/brand/american-holic/search?so=NEW` (new items)
- `https://stripe-club.com/brand/american-holic/search?rd=02&so=PROF` (reservation items)

These return product cards supported by the existing Stripe adapter: seven knit/cardigan products on the sampled new-items page and three on the sampled reservation page. This change replaces the configured landing page with those official entries; adapter scope and price handling are unchanged. Blank prices remain blank. Pagination/exhaustiveness still needs verification.

### Superseded source recovery

Saved recovery state includes obsolete entries, such as DoCLASSE's homepage and Kumikyoku's redirect-loop/oversized old listing. Exact URLs explicitly recorded as `superseded_entry_urls` are moved from active errors/pending pages into `coverage-state.json` → `superseded_sources`, recording the errors, pending flag, superseded date and replacement entries. Source evidence and historical products are retained. The archive survives checkpoints and day changes.

Current configured entries always take precedence over the superseded list. New entry failures and other unresolved URLs are never hidden; new entries must still be fetched before coverage can be complete. Historical or differently parameterized URLs outside the exact list remain unresolved rather than being silently discarded.

## Coverage audit progress

| Brand | Verified evidence | Remaining evidence before certification |
| --- | --- | --- |
| DoCLASSE | Women knit/cardigan entries, card structure, scope-preserving pagination; separate local 11-page probe | Complete NEW/PREORDER surface mapping; production remaining category pages |
| 23ku | Women brand/category entries, card identity/category fields, next-page widget; four-page sample | Remaining category pages and complete NEW/PREORDER scope |
| Kumikyoku | Women brand/category entries, NEW/reservation card badges, next-page widget; four-page sample | Remaining category pages and complete NEW/PREORDER scope |
| AMERICAN HOLIC | Official navigation to NEW and reservation entries, supported knit/cardigan cards | Pagination, full category/surface inventory and gender scope audit |

No `coverage_audit` completion flags are added. The 65-brand inventory in `brand64-source-coverage-diagnosis-20261007.md` remains the baseline; these source repairs are evidence gathering, not a blanket coverage certificate. Strict checks, PUBLISH_HOLD and human review remain enforced.

## Validation and PR #196

75 relevant local tests passed, including 11 added regressions for scoped Onward cards, pagination, bounded reads/redirects, archival/restart/product retention and existing Stripe extraction. Linux PR CI runs the complete Brand64 suite.

PR #196 is still a separate draft and has merge conflicts with current main. Its success summary is emitted before final feed publication, binding and result preservation, so it can say “pipeline SUCCESS” even if a later step fails. Do not adopt it unchanged. If status presentation is revised later, emit the success summary after final preservation and condition it on all required operational outcomes; preserve partial coverage and publication hold.
