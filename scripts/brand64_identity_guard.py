"""Keep roster identities authoritative; retain conflicting facts outside counts."""
import json
from pathlib import Path


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
    decisions_path = Path(__file__).resolve().parents[1]/'config/brand64-identity-resolutions.json'
    decisions = json.loads(decisions_path.read_text()) if decisions_path.exists() else {}
    payload['records'] = apply_identity_resolutions(payload['records'], known, active, decisions)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n')
    (root/'known-products.json').write_text(json.dumps(known, ensure_ascii=False, separators=(',', ':'))+'\n')
    return known, payload['records']


def apply_identity_resolutions(review, known, active, resolutions):
    """Close only exact, evidenced identities; retain every original review record."""
    result = []
    for item in review:
        item = dict(item)
        item.pop('resolution', None)
        item.pop('review_status', None)
        decision = resolutions.get(item.get('identity_key'))
        record = item.get('record', {})
        if item.get('reason') == 'BRAND_IDENTITY_CONFLICT' and decision:
            valid = (decision.get('confirmed_brand_name') == record.get('brand_name')
                     and decision.get('source_url') == record.get('product_url')
                     and bool(decision.get('verified_at_utc')))
            outcome = decision.get('outcome')
            if outcome == 'OUTSIDE_ACTIVE_ROSTER':
                valid = valid and decision['confirmed_brand_name'] not in active.values()
            elif outcome == 'ALREADY_CORRECTED_IN_CANONICAL':
                target = known.get(decision.get('canonical_identity_key'), {})
                valid = valid and target.get('brand_name') == record.get('brand_name') and target.get('product_url') == record.get('product_url') and active.get(target.get('brand_id')) == target.get('brand_name')
            else:
                valid = False
            if valid:
                item['resolution'] = decision
                item['review_status'] = 'RESOLVED'
            else:
                item.pop('resolution', None)
                item.pop('review_status', None)
        result.append(item)
    return result
