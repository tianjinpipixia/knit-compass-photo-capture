#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'brand-intelligence/sirofil-guide.html'


def fail(message: str) -> None:
    raise SystemExit(f'ERROR: {message}')


def main() -> None:
    if not PAGE.exists():
        fail('Sirofil guide page is missing')
    text = PAGE.read_text(encoding='utf-8')
    required = [
        'Siro / Sirofil / Core-spun',
        '短繊維束 ＋ 短繊維束',
        '短繊維束 ＋ フィラメント',
        '中心芯 ＋ 外側短繊維',
        '赛络纺',
        '赛络菲尔纺',
        '包芯纱',
        'Sirofilのフィラメントは必ずしも中心芯として完全被覆されるわけではない',
        'ロービングとの間隔',
        'フィラメント張力',
        './yarn-glossary.html',
        '../owner-yarns/?query=Sirofil',
    ]
    missing = [token for token in required if token not in text]
    if missing:
        fail(f'missing guide tokens: {missing}')
    if '短繊維束×フィラメント' not in text or '芯材＋外側短繊維' not in text:
        fail('Sirofil and core-spun comparison must remain distinct')
    print('sirofil guide: OK (Siro / Sirofil / Core-spun kept distinct)')


if __name__ == '__main__':
    main()
