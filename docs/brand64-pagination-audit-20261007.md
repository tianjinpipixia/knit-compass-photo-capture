# Brand64 registered-listing pagination audit — 2026-10-07

PR #201 production run [37622602894](https://github.com/tianjinpipixia/knit-compass-photo-capture/actions/runs/37622602894) saved 3,346 canonical products and observed 1,553 products across 44 brands. Collection, recovery, owner-screen publication, snapshot binding and preservation succeeded on Ubuntu 26 / Node 24. Strict coverage remained incomplete.

## Live registered-entry audit

Separate direct HTTP verification followed each registered entry's pagination with an 80-page bound per brand. These are local diagnostic counts, not new published canonical totals.

| Brand | Products | Pages fetched | Errors | Pending pages |
| --- | ---: | ---: | ---: | ---: |
| DoCLASSE | 232 | 11 | 0 | 0 |
| 23ku | 274 | 79 | 0 | 0 |
| Kumikyoku | 81 | 23 | 0 | 0 |
| AMERICAN HOLIC (with pagination repair) | 183 | 33 | 0 | 0 |

The first three use unchanged production adapters and registered entries. The AMERICAN HOLIC result uses the narrow repair described below. Product URLs deduplicate through the existing adapters; different adapters retain their existing variant identity rules. Counts therefore are not a cross-brand style comparison.

## Missed AMERICAN HOLIC pagination

The official new-items listing has numbered links and a textless SVG next arrow, with no `rel=next`. The previous scanner recognized neither and reported no pending pages after fetching only the entry page. Its registered new/reservation entry union yielded nine products. The repaired scan yields 183 over 33 pages without errors or pending pages.

Accept numbered or textless links only for the Stripe adapter, AMERICAN HOLIC slug, HTTPS `stripe-club.com` and exact `/brand/american-holic/search` source path. A candidate must increment `page` by exactly one, preserve all other query filters, remain HTTPS and retain the same host/path. This excludes jumps, previous pages, reservation-filter changes and external destinations. Production page/time limits stay unchanged, so production may still legitimately queue later pages.

## Limits of certification

Exhausting these registered listings proves pagination traversal for those entries, not full brand coverage. DoCLASSE navigation separately exposes women new items at `brand_id=1&category_id=502`; that surface has not yet been reconciled against category entries. Onward navigation separately offers reservation filters (`stc=3&ptc=0.1.4`); completeness of category entries versus those filters remains to be checked. AMERICAN HOLIC's `so=NEW` is a sort over an extensive listing, and its `rd=02` entry exposes reservation products; full gender/category inventory still requires evidence.

No `coverage_audit` completion flags are added. `PUBLISH_HOLD` and human review remain required. Local diagnostic products are not imported into the production canonical store or promoted to customer publication.

## Validation

76 relevant local regression tests passed. The new pagination test covers exact increments, unchanged filters, external hosts, changed paths and loop avoidance. A second run after enforcing HTTPS passed all 12 tests in the affected test module. Linux PR CI verifies the complete suite.
