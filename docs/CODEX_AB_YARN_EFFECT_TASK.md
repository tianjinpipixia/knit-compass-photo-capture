# Codex task — AB纱／AB纱效果 classification correction

Repository: `tianjinpipixia/knit-compass-photo-capture`  
Working branch: `agent/fancy-yarn-glossary`  
PR: `#82`

## Goal

Treat `AB纱／AB纱效果` as an **effect term**, not as a synonym for `Siro／赛络纺`.

The business rule is:

- AB effect can be made by plying two differently colored yarns.
- AB effect can also be made by plying different-material yarns.
- Siro / 赛络纺 with two rovings can create an AB effect, but Siro is only one implementation method.
- A/B differentiation may also be introduced at drawing/roving or another upstream process.
- Therefore `AB纱` must never automatically imply Siro, plying, composition, or dye stage.

## Required implementation invariants

1. `brand-intelligence/data/cn-yarn-glossary-wave2.json`
   - Keep `CN-YARN-072` as `AB纱／AB纱效果`.
   - Category must be `⑤ 染色・色効果`.
   - Definition must explicitly state that Siro is only one possible implementation method.
   - Direct search keywords may include AB-specific terms such as `AB纱`, `AB纱效果`, `AB合股纱`, `AB风格`.
   - Do **not** add bare `Siro`, `赛络纺`, `合股`, or `合撚` as AB search keywords because they create false matches.

2. `brand-intelligence/siro-glossary-augment.js`
   - Siro Chinese aliases must remain `赛络纺`, `赛络纺纱`, `赛络纱`, `并捻纺`.
   - `AB纱`, `A，B纱`, `A,B纱` must not be Siro aliases.
   - Siro explanatory copy may mention that AB effect is separate, but Siro technical-card search must not index that explanatory copy.
   - `AB纱` search should return the AB-effect entry without surfacing Siro only because Siro explanatory text mentions AB.
   - `Siro` search should not surface the AB-effect entry merely because its definition lists Siro as one implementation method.
   - Formal-yarn-master candidate matching must use direct names/aliases/search terms, not explanatory process words.

3. PWA/cache
   - Keep the corrected Wave2 version cache-busted in `brand-intelligence/sw.js`.

4. Validation
   - `scripts/validate_yarn_glossary_wave2.py` must guard the AB/Siro separation and direct-search behavior.
   - `scripts/validate_siro_glossary_unification.py` must fail if AB is reintroduced as a Siro alias or explanatory text causes AB-effect search leakage.

## Do not change

- Do not merge PR #82.
- Do not alter formal yarn master data.
- Do not change Human Review status or promotion boundaries.
- Do not collapse Sirofil or Core-spun into Siro.
- Do not generalize supplier-specific terminology into the market dictionary.

## Acceptance criteria

- `AB纱` is shown as an effect term under `⑤ 染色・色効果`.
- `AB纱` is not a Siro alias.
- Search and master matching do not produce generic Siro false positives for AB, or generic AB false positives for Siro.
- Existing 33 base entries remain intact.
- Wave2 contains 13 reviewed entries, for 46 China yarn/material dictionary entries total.
- Siro / Sirofil / Core-spun technical cards remain separate.
- All triggered CI checks pass on the final PR head.

After changes, report the final head SHA, changed files, and CI conclusions. Keep PR #82 as Draft unless the owner explicitly asks to merge.
