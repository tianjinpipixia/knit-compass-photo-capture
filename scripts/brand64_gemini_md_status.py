#!/usr/bin/env python3
"""Current MD status only; legacy primary scans are audit-only."""
import argparse
import json
import os
import pathlib
import subprocess

MD_ROOT = pathlib.Path('data/brand-md-monitoring/gemini-md')
ROOT = pathlib.Path(__file__).resolve().parents[1]
FIELDS = ('gemini_execution_status', 'attempted_brand_count', 'confirmed_brand_count',
          'md_signal_count', 'md_signal_brand_count', 'required_confirmed_brand_count',
          'quota_exhausted', 'errors')


def make_pointer(records):
    # Sort by actual generation, including multiple attempts on the same day.
    records = sorted(records, key=lambda item: (item[1]['generated_at_utc'], item[0]))
    path, artifact = records[-1]
    pointer = {key: artifact[key] for key in FIELDS if key in artifact}
    pointer.update(latest_attempted_scan_date=artifact['observation_date'],
                   generated_at_utc=artifact['generated_at_utc'], artifact_path=path,
                   role='CURRENT_GEMINI_MD_STATUS', analyzer='GEMINI_PRIMARY',
                   pipeline_stage='MD_ANALYSIS', publication_status='PUBLISH_HOLD',
                   human_review_required=True)
    successes = [item for item in records if item[1]['gemini_execution_status'] == 'SUCCESS']
    if successes:
        success_path, success = successes[-1]
        pointer.update(latest_successful_scan_date=success['observation_date'],
                       latest_successful_artifact_path=success_path,
                       latest_successful_generated_at_utc=success['generated_at_utc'])
    return pointer


def local_records(root, repository_root=ROOT):
    records = []
    for path in root.glob('*/gemini-md-*.json'):
        artifact = json.loads(path.read_text())
        if artifact.get('format') == 'KC_BRAND64_GEMINI_MD_FREE_TIER':
            # The runner's default output root is absolute; pointers must survive
            # checkout on another runner or machine (including custom output roots).
            portable_path = pathlib.Path(os.path.relpath(path.resolve(), repository_root)).as_posix()
            records.append((portable_path, artifact))
    return records


def restore():
    def git(*args):
        return subprocess.check_output(['git', *args], text=True)
    refs = git('for-each-ref', '--format=%(refname)', 'refs/remotes/origin/brand64/gemini-md-*').splitlines()
    seen = set()
    for ref in refs:
        for line in git('ls-tree', '-r', ref, '--', str(MD_ROOT)).splitlines():
            meta, path = line.split('\t', 1)
            blob = meta.split()[2]
            if blob in seen or not pathlib.Path(path).match('*/gemini-md-*.json'):
                continue
            seen.add(blob)
            raw = git('show', f'{ref}:{path}')
            artifact = json.loads(raw)
            if artifact.get('format') != 'KC_BRAND64_GEMINI_MD_FREE_TIER':
                continue
            target = pathlib.Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(raw)
    records = local_records(MD_ROOT)
    if records:
        (MD_ROOT / 'latest.json').write_text(json.dumps(make_pointer(records), ensure_ascii=False, indent=2) + '\n')


def summary():
    path = MD_ROOT / 'latest.json'
    if not path.exists():
        return 'Gemini MD: current status unavailable; legacy audit pointer is not used.\n'
    pointer = json.loads(path.read_text())
    return (f"Gemini MD latest attempt: {pointer['latest_attempted_scan_date']} / {pointer['gemini_execution_status']}\n"
            f"Attempt artifact: {pointer['artifact_path']}\n"
            f"Latest SUCCESS: {pointer.get('latest_successful_scan_date', 'UNAVAILABLE')}\n"
            f"Successful artifact: {pointer.get('latest_successful_artifact_path', 'UNAVAILABLE')}\n"
            'CHATGPT_OFFICIAL_DIRECT → GEMINI_PRIMARY (MD_ANALYSIS); PUBLISH_HOLD / Human Review required.\n'
            'gemini-primary-scans: DEPRECATED / AUDIT_ONLY; excluded from current status.\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['restore', 'summary'])
    args = parser.parse_args()
    if args.command == 'restore':
        restore()
    else:
        print(summary(), end='')
