"""Keep roster identities authoritative; retain conflicting facts outside counts."""
import json


def reconcile_identities(known, active, review):
    accepted = {}
    review = list(review)
    for key, original in known.items():
        row = dict(original)
        expected = active.get(row.get('brand_id'))
        name = row.get('brand_name')
        if expected and name in (None, '', row.get('brand_id')):
            history = list(row.get('brand_identity_history') or [])
            if original not in history:
                history.append(original)
            row['brand_identity_history'] = history
            row['brand_name'] = expected
            row['brand_identity_resolution'] = 'ID_PLACEHOLDER_RESOLVED_FROM_ACTIVE_ROSTER'
        if not expected or row.get('brand_name') != expected:
            item = {'reason': 'BRAND_IDENTITY_CONFLICT', 'identity_key': key,
                    'expected_brand_name': expected, 'record': original}
            if item not in review:
                review.append(item)
            continue
        accepted[key] = row
    return accepted, review


def persist_reconciled(root, known, active):
    path = root/'cumulative-products/review-queue.json'
    payload = json.loads(path.read_text()) if path.exists() else {
        'format': 'KC_BRAND64_CANONICAL_REVIEW_QUEUE', 'role': 'NONCOUNTED_EVIDENCE',
        'human_review_required': True, 'records': []}
    known, payload['records'] = reconcile_identities(known, active, payload['records'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n')
    (root/'known-products.json').write_text(json.dumps(known, ensure_ascii=False, separators=(',', ':'))+'\n')
    return known, payload['records']
