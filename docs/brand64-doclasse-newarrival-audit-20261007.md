# DoCLASSE NEW surface reconciliation — 2026-10-07

Official women navigation links `https://www.doclasse.com/item?brand_id=1&category_id=502`. A direct fetch redirected to `https://www.doclasse.com/ladies/feature/newarrival` (retrieved 2026-10-07 12:54:33 UTC; SHA256 `998e825466229b837252694d4d77a997b24ef3e0e5068e0899eb4991f42f8890`).

The NEW page has ten card-verified knit/cardigan products. Nine product codes appear in the separate 232-product, 11-page registered-category traversal; product `33509` does not. The category listing labels its tracking category `レディース/セットアップ`, so the existing category evidence guard rejects it. The NEW page instead explicitly labels this card `レディース/カーディガン`, with exact women brand field, matching product ID/path, name, NEW badge and visible `¥ 5,990 / ￥6,589` price. This is a different official source's explicit evidence, not a name-based override of the category guard.

Add the actual official NEW destination as a third entry. Extend the adapter only to that exact HTTPS host/path with no query parameters. Keep all existing card checks: women brand, knit/cardigan category, no excluded category/name, matching product ID and official path, visible price. Other feature pages, men pages, external hosts and query variants remain unsupported. Category entries retain their current guards.

The live saved-source replay returns ten products, including `33509`, from the new source. This does not certify every NEW/PREORDER surface and does not change publication hold or production budgets. Canonical historical records are preserved.

Validation: all seven affected-module tests passed, including one new scope rejection regression. The wider 81-test local suite had six subtest errors in the unrelated workflow-shell test added by PR #196 because Windows has no Bash runtime; Linux CI is the authority for that test. No local diagnostic products were imported into production.
