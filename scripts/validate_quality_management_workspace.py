#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'quality_management_workspace_v1' / 'index.html'
APP = ROOT / 'quality_management_workspace_v1' / 'app.js'
POLISH = ROOT / 'quality_management_workspace_v1' / 'ui-polish.css'
FABRIC = ROOT / 'fabric-inspection' / 'index.html'


class SurfaceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            self.ids.add(data['id'])
        if tag == 'a' and data.get('href'):
            self.hrefs.append(data['href'])


def parse(path: Path):
    parser = SurfaceParser()
    parser.feed(path.read_text(encoding='utf-8'))
    return parser


def main():
    for path in (INDEX, APP, POLISH, FABRIC):
        assert path.is_file(), f'missing required file: {path.relative_to(ROOT)}'

    index_text = INDEX.read_text(encoding='utf-8')
    app_text = APP.read_text(encoding='utf-8')
    polish_text = POLISH.read_text(encoding='utf-8')
    workspace = parse(INDEX)
    fabric = parse(FABRIC)

    required_workspace_ids = {
        'quality-status', 'analysis', 'testCount', 'appearanceCount', 'improvementCount',
        'pendingCount', 'reviewCount', 'failCount', 'correctionCount', 'recentList',
        'totalCount', 'passCount', 'failRate', 'refreshButton'
    }
    missing_ids = required_workspace_ids - workspace.ids
    assert not missing_ids, f'missing workspace ids: {sorted(missing_ids)}'

    required_links = {
        '../fabric-inspection/#inspectionForm',
        '../fabric-inspection/#defectCategory',
        '../fabric-inspection/#recordList',
        '../status/',
        '../brand-intelligence/',
    }
    missing_links = required_links - set(workspace.hrefs)
    assert not missing_links, f'missing workflow links: {sorted(missing_links)}'

    for target in ('inspectionForm', 'defectCategory', 'recordList'):
        assert target in fabric.ids, f'fabric-inspection target missing: #{target}'

    for label in ('Append Only', 'Audit Log', 'AI Proposal Only', 'Not for Production'):
        assert label in index_text, f'operational boundary label missing: {label}'

    assert 'kc_fabric_inspection_records_v1' in app_text
    assert 'localStorage.getItem' in app_text
    for forbidden in ('localStorage.setItem', 'localStorage.removeItem', 'localStorage.clear', 'fetch(', 'XMLHttpRequest'):
        assert forbidden not in app_text, f'read-only workspace contains write/network operation: {forbidden}'

    assert './ui-polish.css?v=1.0.0' in app_text
    for rule in ('.hero-copy{font-size:14px}', '.side-nav a{font-size:13px}', '.entry-card p{font-size:11px}'):
        assert rule in polish_text, f'readability override missing: {rule}'

    for breakpoint in ('@media(max-width:1020px)', '@media(max-width:760px)', '@media(max-width:470px)'):
        assert breakpoint in index_text, f'responsive breakpoint missing: {breakpoint}'

    assert '試験 → 外観確認 → 改善・訂正履歴' in index_text
    assert '最近の履歴' in index_text
    assert '補助分析を見る' in index_text

    print('PASS: quality workspace routes, read-only boundary, readability, and responsive guards are intact')


if __name__ == '__main__':
    main()
