#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUG = ROOT / 'brand-intelligence/siro-glossary-augment.js'
SHELL = ROOT / 'brand-intelligence/index.html'
GUIDE = ROOT / 'brand-intelligence/siro-sirofil-core-spun.html'


def require(text: str, token: str, label: str) -> None:
    if token not in text:
        raise SystemExit(f'ERROR: missing {label}: {token}')


def main() -> None:
    aug = AUG.read_text(encoding='utf-8')
    shell = SHELL.read_text(encoding='utf-8')
    guide = GUIDE.read_text(encoding='utf-8')

    for token in ['Siro／赛络纺', 'Sirofil／赛络菲尔纺', 'Core-spun／包芯纱']:
        require(aug, token, 'display name')

    for token in ['赛络纺纱', '赛络纱', 'Siro spinning', 'Sirospun', 'サイロ紡績', 'サイロ糸']:
        require(aug, token, 'Siro alias')
    for token in ['赛络菲尔纺', '赛络菲尔纱', 'Sirofil spinning', 'Sirofil yarn', 'サイロフィル紡績', 'サイロフィル糸']:
        require(aug, token, 'Sirofil alias')
    for token in ['包芯纱', '包芯纺', '包芯纱线', 'core-spun', 'core spun yarn', 'core spinning', 'コアスパンヤーン', '芯鞘糸']:
        require(aug, token, 'Core-spun alias')

    require(aug, '短繊維束 × 短繊維束', 'Siro structure')
    require(aug, '短繊維束 × 連続フィラメント', 'Sirofil structure')
    require(aug, '中心芯 ＋ 外側短繊維', 'Core-spun structure')
    require(aug, 'Core-spunへ自動変換しない', 'Sirofil safety rule')
    require(aug, '最終紡績方式＝Ring系／糸構造＝Sirofil', 'Sirofil classification')
    require(aug, '糸構造＝Core-spun。最終紡績方式はRing／Compact／その他を別途確認', 'Core-spun classification')
    require(aug, 'フィラメント供給位置', 'supplier check')
    require(aug, 'ロービングとの間隔', 'supplier check')
    require(aug, '芯材位置', 'supplier check')
    require(aug, '糸構造・複合紡績', 'glossary category')

    require(shell, './siro-glossary-augment.js?v=1.0.0', 'shell script load')
    for token in ['Siro', 'Sirofil', 'Core-spun', '赛络纺', '赛络菲尔纺', '包芯纱']:
        require(guide, token, 'guide alignment')

    # Guard against collapsing Sirofil into a centered-core description.
    sirofil_block = aug.split("id:'KC-SIRO-002'", 1)[1].split("id:'KC-SIRO-003'", 1)[0]
    if '中心芯 ＋ 外側短繊維' in sirofil_block:
        raise SystemExit('ERROR: Sirofil must not use the Core-spun centered-core structure')

    print('OK: unified Siro / Sirofil / Core-spun names, search aliases, card copy, and classification rules')


if __name__ == '__main__':
    main()
