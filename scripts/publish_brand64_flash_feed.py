#!/usr/bin/env python3
"""Atomically publish the read-only owner feed and restart state to one Git branch."""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile

from brand64_flash_pipeline import STATE_FILES

BRANCH = 'brand64/flash-feed'
PREFIX = 'data/brand-md-monitoring/direct-scans/'


def git(*args, env=None, input=None, check=True):
    return subprocess.run(['git', *args], check=check, text=True, input=input,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)


def publish(root):
    names = [*STATE_FILES, 'feed.json', 'latest.json', 'flash-latest.json', 'summary.md']
    for name in names:
        if not (root/name).is_file(): raise ValueError('Missing checkpoint: '+name)
    with tempfile.TemporaryDirectory() as directory:
        env = {**os.environ, 'GIT_INDEX_FILE': str(Path(directory)/'index')}
        # Never force-push: if another run advanced the feed, leave the conflict visible.
        existing = git('ls-remote', '--heads', 'origin', 'refs/heads/'+BRANCH).stdout.strip()
        parent = None
        if existing:
            git('fetch', '--depth=1', 'origin', BRANCH)
            parent = git('rev-parse', 'FETCH_HEAD').stdout.strip()
        git('read-tree', '--empty', env=env)
        for name in names:
            blob = git('hash-object', '-w', str(root/name)).stdout.strip()
            git('update-index', '--add', '--cacheinfo', '100644', blob, PREFIX+name, env=env)
        tree = git('write-tree', env=env).stdout.strip()
        args = ['commit-tree', tree]
        if parent: args += ['-p', parent]
        commit = git(*args, input='Update daily owner flash and recovery state\n').stdout.strip()
        git('push', 'origin', commit+':refs/heads/'+BRANCH)
        print('Published owner flash and recovery state: '+commit)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output-root', type=Path, default=Path('data/brand-md-monitoring/direct-scans'))
    publish(ap.parse_args().output_root)
