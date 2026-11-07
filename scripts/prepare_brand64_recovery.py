"""Prepare an offline, checksum-pinned recovery candidate; never publish it.

All supplied generations contribute products and events. Daily coverage comes
only from the newest actual observation, not from a union of coverage claims.
"""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

from brand64_canonical_store import normalize_identities, preserve, read_pool
from brand64_daily_pipeline_binding import validate_canonical
from brand64_history_store import read_history, write_history
from publish_brand64_flash_feed import build_cumulative_product_shards, build_observed_product_shards

FORMAT = 'KC_BRAND64_RECOVERY_REVIEW_SNAPSHOT'
REVIEW_FILE = 'recovery-review.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':'))+'\n', encoding='utf-8')


def review_metadata(value, redactions, field=''):
    """Keep private laptop/cache paths out of a public review branch."""
    if isinstance(value,dict):
        return {k:review_metadata(v,redactions,field+'.'+k) for k,v in value.items()}
    if isinstance(value,list):
        return [review_metadata(v,redactions,field+'[]') for v in value]
    if (isinstance(value,str) and field.endswith('_path') and
            value.startswith(('/Users/','/private/var/','/var/folders/'))):
        redactions.append({'field':field,'original_value_sha256':hashlib.sha256(value.encode()).hexdigest()})
        return 'local-review:'+Path(value).name
    return value


def pinned_files(root, expected):
    for relative, expected_sha in expected.items():
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts or not expected_sha:
            raise ValueError('Invalid pinned input path/hash')
        if digest(root/path) != expected_sha:
            raise ValueError('RECOVERY_INPUT_CHECKSUM_MISMATCH:'+relative)


def load_source(source, base):
    root = (base/source['root']).resolve()
    pinned_files(root, source['files_sha256'])
    canonical = read_pool(root)
    used = set(source['files_sha256'])
    if canonical is not None:
        manifest = read(root/'cumulative-products/manifest.json')
        used.add('cumulative-products/manifest.json')
        used.update(b['path'] for b in manifest['brands'])
        for item in manifest['daily_sources'].values():
            if digest(root/item['path']) != item['sha256']:
                raise ValueError('RECOVERY_DAILY_SOURCE_CHECKSUM_MISMATCH')
            used.add(item['path'])
    if source.get('archive'):
        archive = (base/source['archive']).resolve()
        if digest(archive) != source['archive_sha256']:
            raise ValueError('RECOVERY_ARCHIVE_CHECKSUM_MISMATCH')
        # Verify the extracted inputs against the pinned original ZIP too.
        with zipfile.ZipFile(archive) as zipped:
            for relative in used:
                if zipped.read(relative) != (root/relative).read_bytes():
                    raise ValueError('RECOVERY_ARCHIVE_CONTENT_MISMATCH:'+relative)
    latest = read(root/'latest.json')
    feed = read(root/'feed.json')
    observed = latest.get('observed_date')
    date.fromisoformat(observed)
    if (latest.get('collector') != 'CHATGPT_OFFICIAL_DIRECT' or
            feed.get('summary', {}).get('observed_date') != observed or
            latest.get('publication_status') != 'PUBLISH_HOLD' or
            latest.get('human_review_required') is not True):
        raise ValueError('RECOVERY_OBSERVATION_PROVENANCE_INVALID')
    if canonical is not None and manifest['observation_date'] != observed:
        raise ValueError('RECOVERY_MANIFEST_DATE_MISMATCH')
    checkpoint = read(root/'known-products.json') if (root/'known-products.json').exists() else {}
    products = normalize_identities(preserve(checkpoint, canonical or {}))
    if not products:
        raise ValueError('RECOVERY_EMPTY_PRODUCT_GENERATION')
    history = read_history(root)
    return {'spec':source, 'root':root, 'latest':latest, 'products':products,
            'canonical':canonical, 'history':history,
            'sort_key':(observed, latest.get('generated_at_utc', ''), source['label'])}


def verify_review(root, expected_manifest_sha, expected_review_sha):
    if digest(root/REVIEW_FILE) != expected_review_sha:
        raise ValueError('RECOVERY_REVIEW_CHECKSUM_MISMATCH')
    review = read(root/REVIEW_FILE)
    if (review.get('format') != FORMAT or review.get('canonical_status') != 'REVIEW_ONLY' or
            review.get('analysis_ready') is not False or review.get('publication_status') != 'PUBLISH_HOLD' or
            review.get('human_review_required') is not True):
        raise ValueError('RECOVERY_REVIEW_STATUS_INVALID')
    if review.get('manifest_sha256') != expected_manifest_sha:
        raise ValueError('RECOVERY_REVIEW_MANIFEST_LEASE_MISMATCH')
    pinned_files(root, review['output_files_sha256'])
    validated = validate_canonical(root, review['observation_date'])
    products, history = read_pool(root), read_history(root)
    if (validated['hashes']['canonical_manifest'] != expected_manifest_sha or
            len(products) != review['product_count'] or len(history) != review['history_event_count']):
        raise ValueError('RECOVERY_REVIEW_COUNT_OR_HASH_MISMATCH')
    return review


def prepare(plan_path, output):
    plan = read(plan_path)
    base = plan_path.parent
    labels = [s['label'] for s in plan['sources']]
    if len(labels) != len(set(labels)) or not all(re.fullmatch(r'[A-Za-z0-9_-]+', x) for x in labels):
        raise ValueError('Invalid/duplicate source labels')
    if output.exists():
        raise ValueError('Recovery output must be a new directory')
    scope_path = (base/plan['scope']['path']).resolve()
    if digest(scope_path) != plan['scope']['sha256']:
        raise ValueError('RECOVERY_SCOPE_CHECKSUM_MISMATCH')
    scope = read(scope_path)
    if scope.get('status') != 'LOCKED_OWNER_APPROVED' or scope['scope_id'] != plan['scope']['scope_id']:
        raise ValueError('RECOVERY_SCOPE_NOT_OWNER_APPROVED')
    sources = sorted([load_source(source, base) for source in plan['sources']], key=lambda s:s['sort_key'])
    if any(output.resolve().is_relative_to(s['root']) for s in sources):
        raise ValueError('Recovery output cannot be inside an input generation')
    latest = sources[-1]
    if not (latest['root']/'coverage-state.json').is_file():
        raise ValueError('Newest actual observation has no coverage checkpoint')
    products, history, details, queue, identity_review = {}, {}, {}, {}, []
    for source in sources:
        products = normalize_identities(preserve(products, source['products']))
        for key, value in source['history'].items():
            if key in history and history[key] != value:
                raise ValueError('RECOVERY_HISTORY_CONFLICT:'+key)
            history[key] = value
        for name, target in [('detail-results.json',details),('deep-dive-queue.json',queue)]:
            path = source['root']/name
            if path.exists():
                target.update(read(path))
        review_path=source['root']/'cumulative-products/review-queue.json'
        if review_path.exists():
            for row in read(review_path)['records']:
                if row not in identity_review: identity_review.append(row)
    # No mutations to an input generation or external service are made.
    output.mkdir(parents=True)
    metadata_redactions=[]
    for source in sources:
        evidence = output/'recovery-evidence'/source['spec']['label']
        write(evidence/'original-products.json', source['products'])
        for name in ['latest.json','feed.json','known-products.json','coverage-state.json','detail-results.json','deep-dive-queue.json','cumulative-products/review-queue.json']:
            if (source['root']/name).is_file():
                (evidence/name).parent.mkdir(parents=True,exist_ok=True)
                write(evidence/name,review_metadata(read(source['root']/name),metadata_redactions,source['spec']['label']+'.'+name))
    for name in ['latest.json','feed.json','flash-latest.json','coverage-state.json','summary.md']:
        source = latest['root']/name
        if source.is_file():
            if source.suffix=='.json':write(output/name,review_metadata(read(source),metadata_redactions,name))
            else:shutil.copy2(source,output/name)
    write(output/'known-products.json',products)
    write(output/'detail-results.json',details)
    write(output/'deep-dive-queue.json',queue)
    write(output/'cumulative-products/review-queue.json',{'format':'KC_BRAND64_CANONICAL_REVIEW_QUEUE',
        'role':'NONCOUNTED_EVIDENCE','human_review_required':True,'records':identity_review})
    write(output/'retrospective-merge-summary.json',{'status':'RECOVERY_FROM_EXISTING_EVIDENCE_ONLY','new_retrospective_claims':0})
    write_history(output,history)
    build_observed_product_shards(output)
    build_cumulative_product_shards(output)
    manifest_path=output/'cumulative-products/manifest.json'
    manifest=read(manifest_path)
    by_identity={r['identity_key']:r for r in identity_review if r.get('reason')=='BRAND_IDENTITY_CONFLICT'}
    manifest['identity_review_product_count']=sum(r.get('review_status')!='RESOLVED' for r in by_identity.values())
    manifest['identity_resolved_product_count']=sum(r.get('review_status')=='RESOLVED' for r in by_identity.values())
    write(manifest_path,manifest)
    exported = read_pool(output)
    if set(exported) != set(products):
        raise ValueError('RECOVERY_PRODUCT_IDENTITY_LOSS')
    for source in sources:
        for key, row in source['products'].items():
            # Normalisation retains complete originals in recovery-evidence.
            if key not in exported:
                raise ValueError('RECOVERY_SOURCE_PRODUCT_MISSING:'+key)
        if any(history.get(k) != v for k,v in source['history'].items()):
            raise ValueError('RECOVERY_SOURCE_HISTORY_MISSING')
    manifest_sha = digest(output/'cumulative-products/manifest.json')
    review = {'format':FORMAT, 'schema_version':'1.0', 'canonical_status':'REVIEW_ONLY',
        'publication_status':'PUBLISH_HOLD','human_review_required':True,'formal_product_registration':False,
        'analysis_ready':False,'observation_date':latest['latest']['observed_date'],
        'daily_observation_source':latest['spec']['label'],'scope_id':scope['scope_id'],
        'expected_canonical_head':plan['expected_canonical_head'],'manifest_sha256':manifest_sha,
        'product_count':len(exported),'history_event_count':len(history),
        'metadata_path_redactions':metadata_redactions,
        'source_provenance':[{'label':s['spec']['label'],'product_count':len(s['products']),
            'history_event_count':len(s['history']),'observed_date':s['latest']['observed_date'],
            'evidence':{k:v for k,v in s['spec'].items() if k not in ['root','archive']}} for s in sources],
        'output_files_sha256':{p.relative_to(output).as_posix():digest(p) for p in sorted(output.rglob('*')) if p.is_file()},
        'not_performed':['canonical branch update','main update','deployment','DB write','publication','Gemini API call'],
        'promotion_rule':'Explicit approval and unchanged expected canonical HEAD are required before any canonical update.'}
    write(output/REVIEW_FILE,review)
    verify_review(output,manifest_sha,digest(output/REVIEW_FILE))
    return review


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--output-root',type=Path,required=True)
    args=parser.parse_args()
    result=prepare(args.plan.resolve(),args.output_root.resolve())
    print(json.dumps({k:result[k] for k in ['product_count','history_event_count','observation_date','manifest_sha256','canonical_status']}))


if __name__ == '__main__': main()
