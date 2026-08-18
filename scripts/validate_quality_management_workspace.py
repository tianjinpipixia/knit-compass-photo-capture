#!/usr/bin/env python3
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / 'quality_management_workspace_v1' / 'index.html'
APP = ROOT / 'quality_management_workspace_v1' / 'app.js'
POLISH = ROOT / 'quality_management_workspace_v1' / 'ui-polish.css'
FABRIC = ROOT / 'fabric-inspection' / 'index.html'
FABRIC_APP = ROOT / 'fabric-inspection' / 'app.js'
MODEL = ROOT / 'fabric-inspection' / 'quality-model.js'
MODEL_TEST = ROOT / 'scripts' / 'validate_quality_model.js'


class SurfaceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if data.get('id'):
            self.ids.add(data['id'])
        if tag == 'a' and data.get('href'):
            self.hrefs.append(data['href'])
        if tag == 'script' and data.get('src'):
            self.scripts.append(data['src'])


def parse(path: Path):
    parser = SurfaceParser()
    parser.feed(path.read_text(encoding='utf-8'))
    return parser


def main():
    for path in (INDEX, APP, POLISH, FABRIC, FABRIC_APP, MODEL, MODEL_TEST):
        assert path.is_file(), f'missing required file: {path.relative_to(ROOT)}'

    index_text = INDEX.read_text(encoding='utf-8')
    app_text = APP.read_text(encoding='utf-8')
    polish_text = POLISH.read_text(encoding='utf-8')
    fabric_text = FABRIC.read_text(encoding='utf-8')
    fabric_app = FABRIC_APP.read_text(encoding='utf-8')
    model_text = MODEL.read_text(encoding='utf-8')
    workspace = parse(INDEX)
    fabric = parse(FABRIC)

    required_workspace_ids = {
        'quality-status', 'analysis', 'testCount', 'appearanceCount', 'reviewQueueCount',
        'improvementCount', 'pendingCount', 'reviewCount', 'failCount', 'openImprovementCount',
        'recentList', 'totalCount', 'passCount', 'failRate', 'approvedCount',
        'closedImprovementCount', 'photoEvidenceCount', 'refreshButton'
    }
    missing_ids = required_workspace_ids - workspace.ids
    assert not missing_ids, f'missing workspace ids: {sorted(missing_ids)}'

    required_links = {
        '../fabric-inspection/?mode=test#inspectionForm',
        '../fabric-inspection/?mode=appearance#inspectionForm',
        '../fabric-inspection/?filter=pending#reviewForm',
        '../fabric-inspection/?filter=improvement#improvementForm',
        '../fabric-inspection/?filter=pending#recordList',
        '../fabric-inspection/?filter=needs-review#recordList',
        '../fabric-inspection/?filter=fail#recordList',
        '../status/',
        '../brand-intelligence/',
    }
    missing_links = required_links - set(workspace.hrefs)
    assert not missing_links, f'missing workflow links: {sorted(missing_links)}'

    required_fabric_ids = {
        'inspectionForm', 'recordList', 'reviewForm', 'improvementForm', 'inspectionScope',
        'testMethod', 'standardValue', 'measuredValue', 'measurementUnit',
        'photoCaptureId', 'qualityPhotoRefs', 'reviewInspectionId', 'reviewDecision',
        'improvementInspectionId', 'cause', 'action', 'verification', 'recordFilter'
    }
    missing_fabric_ids = required_fabric_ids - fabric.ids
    assert not missing_fabric_ids, f'missing fabric workflow ids: {sorted(missing_fabric_ids)}'

    assert '../fabric-inspection/quality-model.js?v=1.1.0' in workspace.scripts
    assert './quality-model.js?v=1.1.0' in fabric.scripts

    for label in ('Append Only', 'Audit Log', 'Human Review', 'Local Device Only'):
        assert label in index_text, f'operational boundary label missing: {label}'
    for phrase in ('この端末内の品質台帳を参照', '自動共有されず', '元の検査記録は上書きせず'):
        assert phrase in index_text, f'local/append-only clarification missing: {phrase}'

    assert 'kc_fabric_inspection_records_v1' in app_text
    assert 'localStorage.getItem' in app_text
    for forbidden in ('localStorage.setItem', 'localStorage.removeItem', 'localStorage.clear', 'fetch(', 'XMLHttpRequest'):
        assert forbidden not in app_text, f'read-only workspace contains write/network operation: {forbidden}'

    for token in ('review_events', 'improvement_events', 'photoEvidenceCount', 'isAppearanceRecord', 'matchesFilter'):
        assert token in model_text, f'quality model capability missing: {token}'

    for append in ('state.records.push(record)', 'state.review_events.push(eventRecord)', 'state.improvement_events.push(eventRecord)'):
        assert append in fabric_app, f'append-only event path missing: {append}'
    for forbidden in ('.splice(', 'state.records[', 'state.review_events[', 'state.improvement_events['):
        assert forbidden not in fabric_app, f'in-place mutation pattern found: {forbidden}'

    for token in ('photo_capture_id', 'photo_refs', 'test_method', 'standard_value', 'measured_value', 'measurement_unit', 'inspection_scope'):
        assert token in fabric_app, f'structured quality field missing from app: {token}'

    for phrase in ('ブラウザLocal Storage保存', 'Human Reviewと改善も別イベントとして追記', '原因 → 改善策 → 担当・期限 → 再試験・効果確認'):
        assert phrase in fabric_text, f'workflow explanation missing: {phrase}'

    assert './ui-polish.css?v=1.1.0' in app_text
    for rule in ('.hero-copy{font-size:14px}', '.side-nav a{font-size:13px}', '.entry-card p{font-size:11px}'):
        assert rule in polish_text, f'readability override missing: {rule}'

    for breakpoint in ('@media(max-width:1020px)', '@media(max-width:760px)', '@media(max-width:470px)'):
        assert breakpoint in index_text, f'responsive breakpoint missing: {breakpoint}'

    print('PASS: quality workspace local boundary, append-only review/improvement flow, structured tests, photo refs, filters, and responsive guards are intact')


if __name__ == '__main__':
    main()
