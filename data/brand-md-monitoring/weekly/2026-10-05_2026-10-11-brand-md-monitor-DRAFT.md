# Brand MD Monitor | Weekly MD DRAFT
Period: 2026-10-05 to 2026-10-11 (Japan)
Status: DRAFT / PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED
Method: analysis of previously saved daily observation artifacts only. No website was revisited.

## Scope and coverage
The saved active roster (updated 2026-10-01) has 65 brands, including JOURNAL STANDARD relume, but the daily Gemini MD analyses contain only 64 brands. This is ROSTER_SCOPE_CONFLICT, not an instruction to delete a brand. Twelve inactive legacy brands are history only.
Each daily direct scan attempted 65 brands and had PARTIAL_COVERAGE with zero fully covered brands. Product-observed brands: Oct 5 40, Oct 6 40, Oct 7 44, Oct 8 39, Oct 9 24, Oct 10 24, Oct 11 23. Counts represent product observations, not sales.
ZARA and SNIDEL have SOURCE_ACCESS_LIMITED on all seven saved Gemini daily analyses. Do not infer their week-over-week product turnover, launches or markdown depth.
PAL ranking movements are not determinable: same-item numeric popularity ranks and same ranking definition were not stored consistently. The external comparison brands PLST, FRAY I.D, H&M, COS, MANGO, NOLLEY'S, BEAUTY&YOUTH have no complete saved daily observations for this period in the checked MD artifacts.

## Evidence-based examples, not proof of weekly launches
- ROPÉ PICNIC: lace layered V-neck knit, ¥5,995, NEW / preorder label: https://www.junonline.jp/rope-picnic/product/tops/knit-sweater/GDM56320
- VIS: side peplum knit, ¥6,589, NEW / preorder: https://www.junonline.jp/vis/product/tops/knit-sweater/BVM46210
- Te chichi: washable, deodorant and antistatic crew cardigan, ¥4,950: https://www.canshop.jp/ap/item/i/A1CAN000A5J3
- 23区: fox cashmere fur gold-button cardigan, ¥34,980, preorder: https://crosset.onward.co.jp/items/KRWOLW0561
- GALLARDAGALANTE: peplum lace knit, ¥28,600, preorder shown for Oct 15: https://www.palcloset.jp/display/item/GGZ1062305A0008/
- LOUNGEDRESS: washable tulle-hem knit, ¥18,700, restock label: https://www.palcloset.jp/display/item/LDZ1062305A0005/
- DISCOAT: color-blocked frill sleeve knit, ¥4,400, NEW: https://www.palcloset.jp/display/item/DCZ1062205A0003/

## Interpretation for yarn and fabric development
1. Examine shape-retaining 12–16G knitting for peplum, lace, collars, and trim: compare plating, PBT core, Milano and full-needle constructions.
2. Compare premium animal-hair products separately from lower-cost feather/shaggy types. Test weight, pilling, shedding, antistatic performance and washing.
3. Keep verified functional claims separate from product-title marketing words.
4. Do not infer demand or sales quantities from SOLD OUT, ranking, site exposure or stock labels.

## Next daily-collection checks
Resolve the 65-versus-64 roster mismatch while retaining all current brands and historical inactive IDs. Restore compliant access to ZARA, SNIDEL and other limited sources. Save actual SKU-level PAL numeric ranking positions and dates. Save ZARA's three and SNIDEL's six official-entry observations per day, plus the seven external brands. Persist exact official URLs, timestamps, product codes, composition, price basis, color and knitting structure. No data gaps may be converted into 'no change'.

## Source files (existing records)
- config/brand64-active-brands.json
- data/brand-md-monitoring/gemini-md/2026-10-05 through 2026-10-11
- data/brand-md-monitoring/direct-scans/2026-10-11/20261010T234419361206Z-check/scan.json
These records reside in existing GitHub snapshot branches named brand64/gemini-md-2026-10-11-38096079609-1 and brand64/direct-38095871622-1.

The full 64-brand weekly comparison cannot be certified because the stored roster and analysis coverage disagree. The monthly report is not due on this (non-first) weekly execution.
