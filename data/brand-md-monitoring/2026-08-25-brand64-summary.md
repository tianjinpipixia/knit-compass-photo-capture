# Brand64 Daily Observation — 2026-08-25

- Observed at: 2026-08-25T08:23:36+09:00
- Scope: WOMEN_KNIT
- Active source: `config/brand64-active-brands.json`
- Light scan: 64 / 64 active brands
- Deep dive: 14 brands
- Current first-seen formal candidates: 2
- Retrospective backfill formal candidates: 10
- Formal product candidates total: 12
- Previous saved observation: 2026-08-24
- Preserved observation gap: 2026-08-22
- Publication: `PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED`
- Sales quantity: `NOT_ESTIMATED`

## Meaningful daily differences

### SNIDEL — 12:00 launch boundary
Two SNIDEL × 近沢レース店 knit cardigans (`SWNT264124`, `SWNT264126`) are confirmed on the official EC with a scheduled sales start of **2026-08-25 12:00**. At the observation time (08:23 JST), both remain `COMING SOON`. They are registered as formal current-first-seen candidates, but **not** as already launched.

### ROPÉ PICNIC — promotion boundary + 2026AW preorder depth
The 8/24 limited promotion boundary has passed. Current official individual pages confirm four 2026AW preorder knit baselines suitable for backfill: `GDM86080`, `GDM86090`, `GDK56520`, `GDK56180`. Promotional expiry is not interpreted as product demand.

### PAL — promotion/ranking updates kept separate from demand
SHENERY's SET UP FAIR boundary, natural couture's current promotion/ranking updates, and DISCOAT's ranking refresh are preserved as exposure/promotion-state changes only. Ranking is **not** treated as sales quantity.

### ZARA — Special Prices freshness recovered
The official Japan Special Prices knit page is current enough to confirm multiple deeply discounted knit listings. This removes yesterday's `PRICE_FRESHNESS_LIMITED` condition for the page itself, but does **not** establish that those markdowns began on 8/25. The regular knit assortment continues to show classic/feminine lace/stripe/polo elements alongside shoulder-structured/asymmetric items.

## Formal product candidates

### Current first-seen
- SNIDEL `SWNT264124` — SNIDEL×近沢レース店 コラボボウタイニットカーディガン
- SNIDEL `SWNT264126` — SNIDEL×近沢レース店 ニットカーディガン

### Retrospective backfill
- ROPÉ PICNIC `GDM86080`
- ROPÉ PICNIC `GDM86090`
- ROPÉ PICNIC `GDK56520`
- ROPÉ PICNIC `GDK56180`
- La boutique BonBon `LBZ1062205A0006`
- La boutique BonBon `LBZ1062205A0014`
- LOUNGEDRESS `LDZ1062305A0005`
- LOUNGEDRESS `LDZ1062205A0006`
- SHENERY `SNZ1062105A0005`
- un dix cors `UOZ1062105A0002`

## MD translation
- **12G–16G:** lace/bow/bijou and compact cardigan structures; keep launch timing and decorative components separate from demand.
- **8G–12G:** feather/hairy and anti-pilling lightweight autumn knit; manage pilling claims/care-note conflicts explicitly.
- **10G–14G:** cotton/acrylic/rayon/polyester transitional blends with home-care value and September/October delivery.
- **High gauge / structured:** mixed-material peplum, tulle/lace connection, shape retention and clean edge stability.

## Data boundaries
- Same URL / same product code is deduplicated.
- Missing composition/function/color is not inferred.
- `SOURCE_STATE_CONFLICT` and stale `COMING SOON`/`本日発売` text are preserved instead of overwritten.
- Existing products are not re-registered unless a meaningful state/price/function/composition delta exists.
- Offline/404 records must be preserved, never deleted.
- 12 inactive legacy brands remain outside active aggregation.
