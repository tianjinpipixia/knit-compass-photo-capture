# Brand64 cumulative observed product pool

The daily `observed-products` index remains a same-day snapshot.

The `cumulative-products` index is a deduplicated MD observation pool built from the durable `known-products.json` baseline. Its identity key is `brand_id|product_url`, so products remain available across days and are updated rather than multiplied when the same official URL is observed again.

This pool is for Brand MD analysis and search only. It is not the formal product master, does not assert that first observation equals sales start, does not estimate sales quantity, and remains `PUBLISH_HOLD / HUMAN_REVIEW_REQUIRED`.
