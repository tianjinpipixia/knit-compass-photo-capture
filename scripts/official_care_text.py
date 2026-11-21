"""Product-bound care declarations on supported non-JUN storefronts."""
import json
import re
import unicodedata
from urllib.parse import urlsplit

CARE_TEXT_ADAPTERS = frozenset(('fr', 'doclasse', 'canshop'))
CARE_TEXT_SOURCE = 'OFFICIAL_PRODUCT_CARE_TEXT'
TOKENS = {
    'home_wash': {
        'hand': {'手洗い', '手洗い可', '手洗い可能', '手洗いOK', '手洗いのみ'},
        'machine': {'洗濯機可', '洗濯機洗い可', '洗濯機洗い', '洗濯機OK', '洗濯機洗い可能',
                    'マシンウォッシャブル', '洗濯機で洗える'},
        'prohibited': {'家庭洗濯不可', '洗濯不可', '水洗い不可', '家庭洗濯禁止'},
    },
    'dry_clean': {
        'allowed': {'ドライクリーニング可', 'ドライクリーニング可能', '石油系ドライクリーニング',
                    '石油系ドライクリーニング可'},
        'prohibited': {'ドライクリーニング不可', 'ドライクリーニング禁止', 'ドライ不可'},
    },
}
DOCLASSE_FUNCTION_LABELS = {
    '接触冷感': ('接触冷感',), '抗菌防臭': ('抗菌', '防臭'), '遮熱': ('遮熱',),
    '吸水速乾': ('吸水速乾',), '帯電防止': ('帯電防止',), '抗ピリング': ('抗ピリング',),
    '洗濯機OK': ('洗濯機洗い可',), 'UVカット': ('UVカット',),
}


def doclasse_features(doc):
    claims = {}
    for node in doc.root.walk():
        if (node.tag != 'p' or not node.parent
                or not node.parent.has_class('detailArea__txt__explain')):
            continue
        label = ' '.join(node.text().split())
        normalized = unicodedata.normalize('NFKC', label)
        if re.fullmatch(r'[0-9]{2,3}%以上UVカット', normalized):
            normalized = 'UVカット'
        for claim in DOCLASSE_FUNCTION_LABELS.get(normalized, ()):
            claims.setdefault(claim, label)
    return claims


def fr_features(text):
    if not isinstance(text, str):
        return {}
    section = re.search(r'【機能と素材について】([^【]*)', text)
    if not section:
        return {}
    for line in re.split(r'<br\s*/?>', section.group(1), flags=re.I):
        line = line.strip().removeprefix('-').strip()
        if line == '熱を外に逃がしにくい保温機能付きなので、寒い時期も温かく着用できます。':
            return {'保温': line}
    return {}


def care_from_text(value):
    if not isinstance(value, str):
        return None
    text = ' '.join(value.split())
    if not text or len(text) > 250:
        return None
    tokens = set(re.split(r'[,、/・\s]+', unicodedata.normalize('NFKC', text).rstrip('。')))
    care = {'status': 'verified', 'evidence_kind': 'official_text', 'source_text': text}
    for field, dictionary in TOKENS.items():
        states = [state for state, labels in dictionary.items() if tokens.intersection(labels)]
        care[field] = states[0] if len(states) == 1 else 'unknown'
    if care['home_wash'] == care['dry_clean'] == 'unknown':
        care['status'] = 'unresolved'
    return care


def texts_from_pair(doc, label, label_tag, value_tag, container_tag):
    result = set()
    for node in doc.root.walk():
        if node.tag != container_tag:
            continue
        cells = [n for n in node.children if getattr(n, 'tag', None) in (label_tag, value_tag)]
        for a, b in zip(cells, cells[1:]):
            if a.tag == label_tag and b.tag == value_tag and ' '.join(a.text().split()) == label:
                result.add(' '.join(b.text().split()))
    return result


def get_fr_care(doc, sku, color):
    for node in doc.root.walk():
        if node.tag != 'script':
            continue
        script = ''.join(x for x in node.children if isinstance(x, str)).lstrip()
        match = re.match(r'window\.__PRELOADED_STATE__\s*=\s*', script)
        if not match:
            continue
        try:
            state = json.JSONDecoder().raw_decode(script, match.end())[0]
            product = state['entity']['pdpEntity'][sku+'-'+color]['product']
        except (KeyError, TypeError, ValueError):
            continue
        if not isinstance(product, dict) or product.get('productId') != sku:
            continue
        text = product.get('washingInformation')
        material_section = next((n for n in doc.root.walk()
                                 if n.attrs.get('id') == 'productMaterialDescription-content'), None)
        if material_section and any(' '.join(n.text().split()) == text for n in material_section.walk() if n.tag == 'p'):
            return product.get('name'), text, fr_features(product.get('longDescription'))
    return None, None, {}


def read_care_detail(doc, url, meta):
    """Only use known official product paths and page-level identity evidence."""
    adapter = meta.get('adapter')
    hosts = {'fr': {'www.uniqlo.com': 'UNIQLO', 'www.gu-global.com': 'GU'},
             'doclasse': {'www.doclasse.com': 'DoCLASSE'}, 'canshop': {'www.canshop.jp': 'Te chichi'}}
    host_map = hosts.get(adapter)
    if not host_map:
        return None
    p = urlsplit(url)
    brand = host_map.get(p.hostname)
    if p.scheme != 'https' or p.username or p.password or p.port or p.query or brand != meta.get('brand_name'):
        return None
    canonical = {urlsplit(n.attrs.get('href', '')) for n in doc.root.walk()
                 if n.tag == 'link' and n.attrs.get('rel') == 'canonical'}
    if len(canonical) != 1:
        return None
    canonical = next(iter(canonical))
    if canonical.scheme != p.scheme or canonical.netloc != p.netloc or canonical.query:
        return None
    path = p.path.rstrip('/')
    claims = {}
    title = next((n.attrs.get('content', '') for n in doc.root.walk()
                  if n.tag == 'meta' and n.attrs.get('property') == 'og:title'), '')
    if adapter == 'fr' and canonical.path.rstrip('/') == path:
        token = re.fullmatch(r'/jp/ja/products/(E[0-9]{6}-[0-9]{3})/([0-9]{2})', path)
        if not token:
            return None
        name, text, claims = get_fr_care(doc, *token.groups())
    elif adapter == 'doclasse':
        token = re.fullmatch(r'(/item/detail/1_1_[0-9]+)(?:/[0-9]+)?', path)
        if not token or canonical.path.rstrip('/') != token[1] or not title.endswith('/DoCLASSE'):
            return None
        vals = texts_from_pair(doc, '洗濯表示', 'th', 'td', 'tr')
        name, text = title.removesuffix('/DoCLASSE'), next(iter(vals)) if len(vals) == 1 else None
        claims = doclasse_features(doc)
    elif adapter == 'canshop' and canonical.path.rstrip('/') == path:
        if not re.fullmatch(r'/ap/item/i/A1CAN[A-Z0-9]+', path) or not title.startswith('Te chichi/'):
            return None
        vals = texts_from_pair(doc, '洗濯表記', 'dt', 'dd', 'dl')
        name, text = title.split('/', 1)[1].split(' | ', 1)[0], next(iter(vals)) if len(vals) == 1 else None
    else:
        return None
    care = care_from_text(text)
    if not isinstance(name, str) or not name.strip() or (not care and not claims):
        return None
    detail = {'product_name': name.strip(), 'product_url': url, 'source_url': url,
              'evidence_level': CARE_TEXT_SOURCE}
    if care:
        detail['care_label'] = care
    if claims:
        detail['function_claims'] = list(claims)
        detail['function_source_text'] = claims
    return detail
