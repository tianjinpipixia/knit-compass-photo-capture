"""Read-only freshness check of the actual product authority, not old main summaries."""
import argparse
import datetime as dt
import json
from pathlib import Path
from brand64_canonical_store import read_pool


def check(root, max_age_days=1):
    records = read_pool(root)
    if records is None:
        raise ValueError('Canonical snapshot is missing')
    manifest = json.loads((root/'cumulative-products/manifest.json').read_text())
    observed = dt.date.fromisoformat(manifest['observation_date'])
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    if not 0 <= (today-observed).days <= max_age_days:
        raise ValueError('Canonical observation date is stale or in the future')
    print(json.dumps({'observation_date':str(observed),'product_count':len(records),'status':'FRESH_CANONICAL_SNAPSHOT','coverage_status':'CHECK_DAILY_SUMMARY_NOT_ASSUMED_COMPLETE'}))

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--max-age-days',type=int,default=1)
    a=p.parse_args();check(a.root,a.max_age_days)
