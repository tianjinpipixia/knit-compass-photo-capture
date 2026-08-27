# Brand64 Daily Observation — 2026-08-26 (retrospective recovery)

- Observation mode: `RETROSPECTIVE_GAP_RECOVERY`
- Recovery date: 2026-08-27
- Scope: WOMEN_KNIT / active Brand64
- Retrospective light check: 64 / 64 active brands
- Deep dive: 7 brands
- Formally confirmed 8/26 first-seen knit candidates: 0
- Formal backfill product candidates: 0
- Publication: `PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED`
- Sales quantity: `NOT_ESTIMATED`

## Why this recovery exists

The scheduled 2026-08-26 freshness run failed before a daily snapshot was saved. The recovery uses only official sources with an explicit 2026-08-26 date or preserved crawl evidence. It does **not** fabricate a historical live-page snapshot and does not interpret missing evidence as “no change.”

## Confirmed 8/26 differences

### ROPÉ PICNIC — special price / coupon state
Official EC shows an **8/26 update** for `MAX70%OFF SPECIAL PRICE` plus a coupon period starting 8/26 12:00. This is stored as a price/promotion-state change, not demand.

### A part by — knit markdown
The official knit list explicitly labels `〖8/26 お値下げ〗アーガイルニットベスト` at **¥5,225 / 36% OFF**. Because an individual product page and product code were not confirmed in this recovery, it is not promoted to a formal product candidate.

### LOUNGEDRESS — new colors / preorder collection
Official 2026.08.26 news says new colors are being added to autumn items including knits and outerwear, with preorder activity. This is preserved at collection level; no knit SKU is invented from the article.

### SHENERY — encore time sale
Official 2026.08.26 news confirms an ENCORE TIME SALE from 8/26 0:00 to 9/1 23:59, with sale items 60% off and up to 70% off. Promotion is separated from product demand.

### WORLD brands — late-summer-to-autumn knit exposure
WORLD’s 2026.08.26 editorial highlights grove’s dry-touch scallop-sleeve knit and SHOO・LA・RUE’s cool/washable/UV color-block bow-tie knit. This is editorial exposure, not a new-product launch claim.

### SNIDEL — post-launch source-state conflict
The 8/25 12:00 launch boundary for the SNIDEL × 近沢レース店 knit cardigans has passed, but older cached individual pages still show `COMING SOON` while newer listings continue reservation/new exposure. The conflict is preserved; the same product codes are not re-registered as 8/26 new products.

## Data boundaries

- Explicit 8/26 evidence is separated from undated current-page state.
- Brands without reconstructable 8/26 evidence are `SOURCE_FRESHNESS_LIMITED_RETROSPECTIVE`, not “no change.”
- Article/listing evidence without individual product code + official product page is not promoted to a formal product candidate.
- Promotion, ranking, and editorial exposure are not used as sales-quantity evidence.
- Same product URL/code remains deduplicated.
