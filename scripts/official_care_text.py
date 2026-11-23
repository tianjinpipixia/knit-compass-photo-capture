"""Product-bound care declarations on supported non-JUN storefronts."""
import json
import html
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from brand_direct_adapters import matches

CARE_TEXT_ADAPTERS = frozenset(('fr', 'doclasse', 'canshop', 'pal', 'dot', 'stripe', 'baycrews',
                               'urbanresearch', 'onward', 'mix_care', 'ikka', 'usagi', 'unitedarrows'))
CARE_TEXT_SOURCE = 'OFFICIAL_PRODUCT_CARE_TEXT'
ONWARD_HOST = 'crosset.onward.co.jp'
USAGI_HOST = 'usagi-online.com'
UNITED_ARROWS_HOST = 'store.united-arrows.co.jp'
UNITED_ARROWS_VARIANT_QUERY = {'areaid': r'ebGL[0-9]+', 'clr_id': r'[0-9]{3}'}
USAGI_ASSET_ROOT = '/res/p/img/item/washing/'
USAGI_ASSET_VERSION = '20241212'
MIX_CARE_CONFIG = 'config/brand64-mix-care-codes.json'
PETROLEUM_DRY_LABELS = {'ドライクリーニング(石油系)', 'ドライ石油系'}
TOKENS = {
    'home_wash': {
        'hand': {'手洗い', '手洗い可', '手洗い可能', '手洗いOK', '手洗いのみ'},
        'machine': {'洗濯機可', '洗濯機洗い可', '洗濯機洗い', '洗濯機OK', '洗濯機洗い可能',
                    'マシンウォッシャブル', '洗濯機で洗える'},
        'prohibited': {'家庭洗濯不可', '洗濯不可', '水洗い不可', '家庭洗濯禁止'},
    },
    'dry_clean': {
        'allowed': {'ドライクリーニング可', 'ドライクリーニング可能', '石油系ドライクリーニング',
                    '石油系ドライクリーニング可'} | PETROLEUM_DRY_LABELS,
        'prohibited': {'ドライクリーニング不可', 'ドライクリーニング禁止', 'ドライ不可'},
    },
}
DOCLASSE_FUNCTION_LABELS = {
    '接触冷感': ('接触冷感',), '抗菌防臭': ('抗菌', '防臭'), '遮熱': ('遮熱',),
    '吸水速乾': ('吸水速乾',), '帯電防止': ('帯電防止',), '抗ピリング': ('抗ピリング',),
    '洗濯機OK': ('洗濯機洗い可',), 'UVカット': ('UVカット',),
}
FR_FEATURE_LINES = {
    '熱を外に逃がしにくい保温機能付きなので、寒い時期も温かく着用できます。': ('保温',),
    'ご家庭の洗濯機でそのまま洗えるマシンウォッシャブル機能付きです。': ('洗濯機洗い可',),
    '毛玉になりにくいアンチピリング素材を使用しています。': ('抗ピリング',),
}
STRIPE_FEATURE_LINES = {
    '静電気防止(バイパチニット)': ('帯電防止',),
    '毛玉防止': ('抗ピリング',),
    '毛玉ができにくいアンチピリング素材です。': ('抗ピリング',),
    'ご家庭の洗濯機でお洗濯して頂けるニットです。': ('洗濯機洗い可',),
    'ご家庭の洗濯機でお洗濯して頂けます。': ('洗濯機洗い可',),
    'マシンウォッシャブル:ご家庭の洗濯機でお洗濯して頂けます。': ('洗濯機洗い可',),
}
STRIPE_WASH_FEATURE_HEADER = '・ウォッシャブルニット'
STRIPE_WASH_FEATURE_SENTENCE = 'ご家庭の洗濯機でお洗濯して頂けるニットです。'
STRIPE_WASH_NET_NOTE = '洗濯ネットをご使用頂き、形を整えて陰平干しして頂くのがおすすめです。'
FUNCTION_LABELS = {
    **DOCLASSE_FUNCTION_LABELS,
    **FR_FEATURE_LINES,
    **STRIPE_FEATURE_LINES,
    'マシンウォッシャブル': ('洗濯機洗い可',), '洗濯機可': ('洗濯機洗い可',),
    '洗濯機洗い可': ('洗濯機洗い可',), '洗濯機可能': ('洗濯機洗い可',),
    '手洗い可': ('手洗い可',), '手洗い可能': ('手洗い可',),
    '抗ピル': ('抗ピリング',), '毛玉軽減': ('抗ピリング',),
    '毛玉になりにくい': ('抗ピリング',), 'アンチピリング': ('抗ピリング',),
    '静電気防止': ('帯電防止',), '制電': ('帯電防止',), 'UVケア': ('UVカット',),
    '保温': ('保温',), '防臭': ('防臭',),
}


def named_features(labels):
    return {claim: label for label in labels
            for claim in FUNCTION_LABELS.get(unicodedata.normalize('NFKC', label.strip()), ())}


def title_features(title):
    blocks = re.findall(r'【([^】]+)】|〖([^〗]+)〗|《([^》]+)》|≪([^≫]+)≫', title)
    return named_features(label for block in blocks
                          for label in re.split(r'[/／・、]', next(x for x in block if x)))


def add_world_listing_features(record, meta):
    if (meta.get('adapter') != 'world' or record.get('evidence_level') != 'OFFICIAL_LISTING_CARD'
            or record.get('scope_status') != 'BRAND_AND_KNIT_PATH_MATCHED'
            or not re.fullmatch(r'[a-f0-9]{64}', str(record.get('source_sha256', '')))):
        return
    product = urlsplit(record['product_url'])
    source = urlsplit(record['source_url'])
    if any(u.scheme != 'https' or u.netloc != 'store.world.co.jp' for u in (product, source)):
        return
    slug = re.escape(meta['slug'])
    if (not re.fullmatch(r'/brand/'+slug+r'/item/[0-9A-Za-z]+/?', product.path)
            or not re.fullmatch(r'/s/brand/'+slug+r'/category/WB/WB\d+/+', source.path)
            or not meta.get('women_category_entry')):
        return
    claims = title_features(record['product_name'])
    if claims:
        record['function_claims'] = list(dict.fromkeys([*(record.get('function_claims') or []), *claims]))
        record['function_listing_evidence'] = {'source_url': record['source_url'],
            'source_sha256': record['source_sha256'], 'title': record['product_name'], 'claim_text': claims}


# JIS L0001 codes from the storefronts' official product care declarations.
JIS_HOME = {
    '100': ('prohibited', None, None), '110': ('hand', 40, None), '111': ('hand', 30, None),
    '130': ('machine', 30, None), '131': ('machine', 30, 'gentle'), '132': ('machine', 30, 'very_gentle'),
    '140': ('machine', 40, None), '141': ('machine', 40, 'gentle'), '142': ('machine', 40, 'very_gentle'),
    '150': ('machine', 50, None), '151': ('machine', 50, 'gentle'),
    '160': ('machine', 60, None), '161': ('machine', 60, 'gentle'), '170': ('machine', 70, None),
}
JIS_DRY = {
    '600': ('prohibited', None, None), '610': ('allowed', 'F', None), '611': ('allowed', 'F', 'gentle'),
    '620': ('allowed', 'P', None), '621': ('allowed', 'P', 'gentle'),
}


def jis_care_text(value, text_format):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r'洗濯記号 ([1-7][0-9]{2}(?:,[1-7][0-9]{2}){0,19})', value)
    if not match:
        return None
    parts = match[1].split(',')
    home_codes = [code for code in parts if code.startswith('1')]
    dry_codes = [code for code in parts if code.startswith('6')]
    home = JIS_HOME.get(home_codes[0]) if len(home_codes) == 1 else None
    dry = JIS_DRY.get(dry_codes[0]) if len(dry_codes) == 1 else None
    return {'status': 'verified' if home or dry else 'unresolved', 'evidence_kind': 'official_text',
            'text_format': text_format, 'source_text': value,
            'home_wash': home[0] if home else 'unknown', 'dry_clean': dry[0] if dry else 'unknown',
            **({k: v for k, v in zip(('max_water_c', 'home_cycle'), home[1:]) if v} if home else {}),
            **({k: v for k, v in zip(('dry_solvent', 'dry_cycle'), dry[1:]) if v} if dry else {})}


# The exact SVG bytes were checked against the USAGI ONLINE laundry guide.
# Only the home washing and dry cleaning assets supply a code.
USAGI_ICONS = {
    'ua': ('110', '66165572147221fdd68c2b34fd5d3f16ebe85522ce711c97335975a16cc473d8'),
    'ub': ('100', 'ae121a65dd179926d5021b364a213494af22c456f33849748188a324b2beb91b'),
    'ue': ('132', '38e3bdcc8ab1e96bed4ea78284a68a40f729fe99e98f12364cdb0135451a7527'),
    'a': ('600', '3c2686e9c91dfbb33dae91ea6ebd631821eb543d9c54c8a8aacd015759b6d04c'),
    'c': ('621', '5753ad07e6e79259d3803f053bfc3a7b625716bf6163158962452a217878c8cb'),
    'e': ('611', '157f1166cf8923d65f4b521f8c93197fcc7bf12f253ad9644cfe24567d51883f'),
    'ui': (None, '5aca1f94d1451603ef3258d54d41eab6bb1df75531c8d801c8f021a77a5ee4f6'),
    'ul': (None, '2d06f2b5e9ae1f04aab41331085542628b8fe88c7bfe120a95c90f5ecf5c0199'),
    'up': (None, 'c217ffc44d2c0ebdf35ea7511856207f3eda18ddf239e104bc4533ed45f722ea'),
    'ut': (None, 'a5bc3873efb850e61471fd427f807ba5b84b0345235de5ee0a514c0aecd5297e'),
    'uw': (None, '0dbc7a0c83be8c62bf6687141c9dd850f2f9afdf7475eff2834ded15b561a005'),
    'ux': (None, '10391baf11a819f831fa65513478f9c663d330544731ce5e34e19077c589b236'),
    'uy': (None, '534dd760e2c7a2ac92b13fb7c9de0ee8bde14296a345c817e70dff9c8a6ad568'),
    'f': (None, '85dfbfa55fa8b5b5d21464f4e4b0b97286167c28fe9ad9167426d41e457727f5'),
    'i': (None, 'ee2862fd9d4960580e1d645ab1e4ddaecfbe9e57d02d52706c0cdc46d5bf1c0b'),
}


def usagi_icon_url(name):
    return f'https://{USAGI_HOST}{USAGI_ASSET_ROOT}{name}.svg?{USAGI_ASSET_VERSION}'


def usagi_symbol_care(groups):
    if not isinstance(groups, list) or not groups or len(groups) > 24:
        return None
    codes = set()
    for group in groups:
        if not isinstance(group, str):
            return None
        names = group.split(',')
        if len(names) > 12 or len(set(names)) != len(names) or not set(names) <= USAGI_ICONS.keys():
            return None
        parsed = {code for name in names if (code := USAGI_ICONS[name][0])}
        if sum(code.startswith('1') for code in parsed) != 1 or sum(code.startswith('6') for code in parsed) != 1:
            return None
        codes.update(parsed)
    care = jis_care_text('洗濯記号 '+','.join(sorted(codes)), 'usagi_symbols')
    if not care or care['status'] != 'verified':
        return None
    return {**care, 'icon_groups': sorted(set(groups))}


def usagi_detail(doc, url, meta, path, title, read_care_image_sha):
    prefix = {'snidel': 'SND', 'milaowen': 'MOW'}.get(meta.get('slug'))
    title_parts = title.split('｜')
    if (not prefix or not re.fullmatch(r'/brand/'+meta['slug']+r'/item/'+prefix+r'[0-9]{4}[A-Z][0-9]{4}', path)
            or len(title_parts) < 2 or not matches(title_parts[1].split('（')[0], meta)):
        return None
    sections = [node for node in doc.root.walk() if node.has_class('info-washing')]
    headings = {node.text().strip() for node in doc.root.walk() if node.tag == 'h1' and node.text().strip()}
    if len(sections) != 1 or len(headings) != 1 or not read_care_image_sha:
        return None
    groups = []
    file_pattern = re.compile(re.escape(USAGI_ASSET_ROOT)+r'([a-z0-9]{1,4})\.svg\?'+USAGI_ASSET_VERSION)
    for node in sections[0].walk():
        if not node.has_class('washing-sku-group'):
            continue
        imgs = [child for box in node.walk() if box.has_class('washing-icons')
                for child in box.walk() if child.tag == 'img']
        icons = [file_pattern.fullmatch(image.attrs.get('src') or '') for image in imgs]
        if not node.attrs.get('data-sku-color') or not icons or not all(icons):
            return None
        groups.append(','.join(icon[1] for icon in icons))
    care = usagi_symbol_care(groups)
    if not care:
        return None
    used = {name for group in groups for name in group.split(',')}
    try:
        if any(read_care_image_sha(usagi_icon_url(name)) != USAGI_ICONS[name][1] for name in sorted(used)):
            return None
    except (OSError, ValueError):
        return None
    name = headings.pop()
    return assemble_detail(name, url, care, title_features(name))


def dot_detail_request(html, url, meta):
    source = urlsplit(url)
    slug = meta.get('slug', '')
    path = source.path.rstrip('/') + '/'
    code = re.fullmatch(r'/' + re.escape(slug) + r'/disp/item/([0-9]{5,12})/', path)
    if source.scheme != 'https' or source.netloc != 'www.dot-st.com' or source.query or not code:
        return None
    raw = re.search(r'function getItemDetailData\(timing\).*?let sendData\s*=\s*({[^}]{1,1200}})', html, re.S)
    if not raw:
        return None
    try:
        params = json.loads(re.sub(r'("eafgrnl"\s*:)\s*eafgrnl', r'\1""', raw[1]))
    except ValueError:
        return None
    if (params.get('itemCd') != code[1] or params.get('shopDir') != slug or params.get('ga_url') != path
            or not re.fullmatch(r'[0-9]{10}', str(params.get('shopNo')))
            or not re.fullmatch(r'[A-Z0-9]{2}', str(params.get('colorCd')))
            or not re.fullmatch(r'[0-9]{14}', str(params.get('lm')))):
        return None
    request = {key: params[key] for key in ('itemCd', 'shopDir', 'shopNo', 'colorCd', 'ga_url', 'lm')}
    request.update(dict.fromkeys(('dispNo', 'enmlcd', 'enemtp', 'eafgrnl'), ''))
    return 'https://www.dot-st.com/async/cb/item/sub/?' + urlencode(request)


def dot_detail(body, product_url, request_url, meta):
    params = parse_qs(urlsplit(request_url).query)
    try:
        data = json.loads(body)
        items = data['resultDtl']['item']
    except (ValueError, KeyError, TypeError):
        return None
    if data.get('result') != 'true' or not isinstance(items, list) or len(items) != 1:
        return None
    item = items[0]
    if (not isinstance(item, dict) or [item.get('itemCd')] != params.get('itemCd')
            or [item.get('manShopNo')] != params.get('shopNo')
            or not isinstance(item.get('brandNm'), str) or not matches(item['brandNm'], meta)
            or not isinstance(item.get('itemNm'), str) or not item['itemNm'].strip()):
        return None
    care = jis_care_text('洗濯記号 ' + str(item.get('washIcon', '')), 'dot_symbols')
    tags = item.get('tagFunctionList')
    claims = named_features(tag['tagName'] for tag in tags
                            if isinstance(tag, dict) and isinstance(tag.get('tagName'), str)) if isinstance(tags, list) else {}
    detail = assemble_detail(item['itemNm'], product_url, care, claims)
    material = item.get('ingredient')
    if isinstance(material, str):
        material = ' '.join(html.unescape(re.sub(r'<br\s*/?>', ' ', material, flags=re.I)).split())
        if re.search(r'\d\s*[%％]', material) and '<' not in material:
            if detail is None:
                detail = {'product_name':item['itemNm'].strip(), 'product_url':product_url,
                          'source_url':product_url, 'evidence_level':CARE_TEXT_SOURCE}
            detail = with_composition(detail, {material})
    return detail


def doclasse_feature_labels(label):
    normalized = unicodedata.normalize('NFKC', label)
    if re.fullmatch(r'[0-9]{2,3}%以上UVカット', normalized):
        normalized = 'UVカット'
    return DOCLASSE_FUNCTION_LABELS.get(normalized, ())


def doclasse_features(doc):
    claims = {}
    for node in doc.root.walk():
        if (node.tag != 'p' or not node.parent
                or not node.parent.has_class('detailArea__txt__explain')):
            continue
        label = ' '.join(node.text().split())
        for claim in doclasse_feature_labels(label):
            claims.setdefault(claim, label)
    return claims


def fr_features(text):
    if not isinstance(text, str):
        return {}
    section = re.search(r'【機能と素材について】([^【]*)', text)
    if not section:
        return {}
    lines = re.split(r'<br\s*/?>|[\r\n]+', section.group(1), flags=re.I)
    phrases = (line.strip().removeprefix('-').strip() for line in lines)
    return {claim: phrase for phrase in phrases for claim in FR_FEATURE_LINES.get(phrase, ())}


def fr_washing_field(value):
    if value == '洗濯機':
        return {'status': 'verified', 'evidence_kind': 'official_text', 'text_format': 'fr_washing_field',
                'source_text': value, 'home_wash': 'machine', 'dry_clean': 'unknown'}
    return care_from_text(value)


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
    if care['dry_clean'] == 'allowed' and tokens.intersection(PETROLEUM_DRY_LABELS):
        care['dry_solvent'] = 'F'
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


PAL_DRY = re.compile(r'ドライクリーニング(?:[、,](?:ウエット|ウェット)クリーニング)?'
                     r'\s*:?[ \t]*(可能|可|不可)(?:\(弱い処理\))?')
PAL_PETROLEUM = re.compile(r'ドライクリーニング:\s*石油系溶剤\s+弱い処理')
PAL_HAND_LIMIT = re.compile(r'手洗い(?:可能|可):\s*(30|40)°C\s*限度')
PAL_DRY_ONLY = re.compile(r'(?:家庭洗濯機[×✕]|家庭洗濯不可)\s*\(ドライクリーニングのみ可能\)')


def pal_care_text(original, text_format='pal_care'):
    if not isinstance(original, str) or not 0 < len(original) <= 250:
        return None
    parsed = set()
    temperatures = set()
    lines = original.split(' ／ ')
    for line in lines:
        value = unicodedata.normalize('NFKC', line)
        if text_format == 'pal_care_v2':
            value = value.strip().lstrip('・■●').strip()
        value = re.sub(r'^(?:本体|製品):\s*', '', value)
        if text_format == 'pal_care_v2':
            dry = PAL_DRY.fullmatch(value)
            if dry:
                parsed.add('ドライクリーニング不可' if dry[1] == '不可' else 'ドライクリーニング可')
                continue
            if PAL_PETROLEUM.fullmatch(value):
                parsed.add('石油系ドライクリーニング可')
                continue
            if PAL_DRY_ONLY.fullmatch(value):
                parsed.update(('家庭洗濯不可', 'ドライクリーニング可'))
                continue
            hand = PAL_HAND_LIMIT.fullmatch(value)
            if hand:
                parsed.add('手洗い可')
                temperatures.add(int(hand[1]))
                continue
        value = re.sub(r'洗濯機洗い\((?:弱|非常に弱い)\)', '洗濯機洗い', value)
        for piece in re.split(r'[/,・、()]+', value):
            token = piece.strip()
            parsed.add({'洗濯機洗濯': '洗濯機洗い', 'ドライクリーニング': 'ドライクリーニング可'}.get(token, token))
    # A product may explicitly permit hand washing in addition to an official
    # machine-wash classification in the product's item table.
    if (re.match(r'^本体:洗濯機洗い(?:\(|可能|可|$)', unicodedata.normalize('NFKC', lines[0]))
            and not parsed.intersection({'手洗い', '手洗いのみ'})):
        parsed.difference_update({'手洗い可', '手洗い可能'})
    care = care_from_text(' '.join(sorted(parsed)))
    if care and care['home_wash'] == 'hand' and len(temperatures) == 1:
        care['max_water_c']=temperatures.pop()
    return {**care, 'source_text': original, 'text_format': text_format} if care else None


def product_jsonld(doc, kind):
    for node in doc.root.walk():
        if node.tag != 'script' or node.attrs.get('type') != 'application/ld+json':
            continue
        try:
            data = json.loads(''.join(x for x in node.children if isinstance(x, str)))
        except ValueError:
            continue
        for item in data if isinstance(data, list) else [data]:
            if isinstance(item, dict) and item.get('@type') == kind:
                yield item


def pal_detail(doc, code, meta):
    for group in product_jsonld(doc, 'ProductGroup'):
        if group.get('productGroupID') != code:
            continue
        brand = group.get('brand')
        if (not isinstance(brand, dict) or not isinstance(brand.get('name'), str)
                or not matches(re.split(r'[（(]', brand['name'], maxsplit=1)[0], meta)):
            continue
        name = group.get('name')
        if not isinstance(name, str):
            continue
        values = []
        for table in doc.root.walk():
            if table.tag != 'table':
                continue
            rows = {}
            for row in table.walk():
                if row.tag != 'tr':
                    continue
                cells = [n for n in row.children if getattr(n, 'tag', None) in ('th', 'td')]
                if len(cells) == 2 and cells[0].tag == 'th' and cells[1].tag == 'td':
                    rows[' '.join(cells[0].text().split())] = ' '.join(cells[1].text().split())
            if rows.get('品番') == code and rows.get('取り扱い') not in (None, '-'):
                values.append(rows['取り扱い'])
        description = group.get('description')
        if isinstance(description, str):
            values.extend(re.findall(r'^[ \t]*(?:[■●][ \t]*)?(?:洗濯(?:方法|表示|表記)?|'
                                     r'お手入れ方法|取り扱い)[：:]([^\r\n]+)', description, re.M))
            instructions = html.unescape(re.sub(r'<br\s*/?>', '\n', description, flags=re.I)).splitlines()
            for line in instructions:
                bullet = re.fullmatch(r'[・■●]\s*(.+)', unicodedata.normalize('NFKC', line).strip())
                if bullet and (bullet[1] == '家庭洗濯不可' or any(
                        pattern.fullmatch(bullet[1]) for pattern in (PAL_DRY, PAL_PETROLEUM, PAL_HAND_LIMIT))):
                    values.append(line.strip())
        material = group.get('material')
        if isinstance(material, str):
            values.extend(re.findall(r'^[ \t]*(?:手洗い(?:可能|可)?|家庭洗濯不可|洗濯機洗い(?:可能|可)?|'
                                     r'ドライクリーニング)[ \t\u3000]*[（(][^\r\n]+[）)]\s*$', material, re.M))
        originals = list(dict.fromkeys(value.strip() for value in values if value.strip() and len(value.strip()) <= 120))
        return name, pal_care_text(' ／ '.join(originals), 'pal_care_v2'), title_features(name)
    return None, None, {}


def stripe_care_text(original):
    if not isinstance(original, str):
        return None
    matched = re.fullmatch(r'液温は(30|40)°Cを限度とし、手洗いが可能です。 / '
                           r'ドライクリーニングは可能です。\(溶剤は石油系を使用してください\)',
                           unicodedata.normalize('NFKC', original))
    if not matched:
        return None
    return {'status':'verified','evidence_kind':'official_text','text_format':'stripe_instructions',
            'source_text':original,'home_wash':'hand','max_water_c':int(matched[1]),
            'dry_clean':'allowed','dry_solvent':'F'}


def stripe_wash_feature_care(original):
    if original not in (STRIPE_WASH_FEATURE_HEADER+' ／ '+STRIPE_WASH_FEATURE_SENTENCE,
                         STRIPE_WASH_FEATURE_HEADER+' ／ '+STRIPE_WASH_FEATURE_SENTENCE+STRIPE_WASH_NET_NOTE):
        return None
    return {'status': 'verified', 'evidence_kind': 'official_text', 'text_format': 'stripe_wash_feature',
            'source_text': original, 'home_wash': 'machine', 'dry_clean': 'unknown'}


def stripe_wash_feature(instructions):
    if re.search(r'家庭洗濯不可|水洗い不可|手洗いのみ|洗濯機(?:洗い|の使用)(?:は)?(?:不可|禁止)|'
                 r'洗濯機で(?:は)?(?:洗えません|洗えない)', instructions):
        return None
    section = re.search(r'(?m)^[ \t]*■機能[ \t]*$', instructions)
    if not section:
        return None
    lines = [line.strip() for line in instructions[section.end():].splitlines() if line.strip()]
    for label, declaration in zip(lines, lines[1:]):
        if label.startswith(('■', '【', '※', '透け感')):
            break
        if label == STRIPE_WASH_FEATURE_HEADER:
            return stripe_wash_feature_care(label+' ／ '+declaration)
    return None


def stripe_detail(doc, url, slug):
    expected = urlsplit(url).path.rstrip('/')
    if not re.fullmatch('/brand/'+re.escape(slug)+r'/item/[0-9A-Za-z]+', expected):
        return None
    for listing in product_jsonld(doc, 'Product'):
        if listing.get('url') not in (url, url.rstrip('/')+'/'):
            continue
        name = listing.get('name')
        if not isinstance(name, str) or not name.strip():
            continue
        claims = title_features(name)
        care = None
        description = listing.get('description')
        if isinstance(description, str):
            instructions = html.unescape(re.sub(r'<[^>]+>', '\n', description))
            for line in instructions.splitlines():
                statement = line.strip().removeprefix('・').strip()
                for claim in STRIPE_FEATURE_LINES.get(unicodedata.normalize('NFKC', statement), ()):
                    claims.setdefault(claim, statement)
            prose = html.unescape(re.sub(r'<[^>]+>', ' ', description))
            for cue, claim in {
                'マシンウォッシャブル：ご家庭の洗濯機でお洗濯して頂けます': '洗濯機洗い可',
                'ご家庭の洗濯機で洗える仕様': '洗濯機洗い可',
                '静電気防止機能付き': '帯電防止',
            }.items():
                if cue in prose:
                    claims.setdefault(claim, cue)
            heading = re.search(r'(?m)^\s*(?:■|【)お洗濯について】?\s*$', instructions)
            if heading:
                text = instructions[heading.end():]
                wash = re.findall(r'(?m)^\s*・(液温[^\n]+手洗いが可能です。)\s*$', text)
                dry = re.findall(r'(?m)^\s*・(ドライクリーニングは可能です。[^\n]+)\s*$', text)
                if len(wash) == len(dry) == 1:
                    care = stripe_care_text(wash[0].strip()+' ／ '+dry[0].strip())
            elif not re.search(r'【(?:先行)?予約[^】]*】|〖(?:先行)?予約[^〗]*〗', name):
                care = stripe_wash_feature(instructions)
                if care:
                    claims.setdefault('洗濯機洗い可', STRIPE_WASH_FEATURE_SENTENCE)
        return assemble_detail(name, url, care, claims)
    return None


def baycrews_detail(doc, code, slug, path, title, meta):
    match = re.fullmatch(r'/item/detail/'+re.escape(slug)+r'/[a-z0-9-]+/'+code, path)
    parts = title.split('｜')
    if (not match or len(parts) < 3 or not parts[-1].startswith('BAYCREW')
            or not matches(re.split(r'[（(]', parts[-2], maxsplit=1)[0], meta)):
        return None, None
    detail = [node for node in doc.root.walk() if node.tag == 'dl' and node.has_class('dataDetail')
              and any(n.attrs.get('id') == 'itemid' and n.text().strip() == code for n in node.children
                      if getattr(n, 'tag', None) == 'dd')]
    if len(detail) != 1:
        return None, None
    cells = [n for n in detail[0].children if getattr(n, 'tag', None) in ('dt', 'dd')]
    values = {' '.join(b.text().split()) for a, b in zip(cells, cells[1:])
              if a.tag == 'dt' and b.tag == 'dd' and a.text().strip() == '取扱い'}
    value = next(iter(values)) if len(values) == 1 else None
    return parts[0], pal_care_text(value, 'official_store_care')


def urban_detail(doc, url, meta):
    path = urlsplit(url).path.rstrip('/')
    code = re.fullmatch(r'/shop/g/g([A-Z0-9-]{8,32})', path)
    if not code:
        return None
    for item in product_jsonld(doc, 'Product'):
        brand = item.get('brand')
        if not isinstance(brand, dict) or not isinstance(brand.get('name'), str) or not matches(brand['name'], meta):
            continue
        name = item.get('name')
        if not isinstance(name, str) or not name.strip():
            continue
        values = set()
        for section in doc.root.walk():
            if not section.has_class('block-goods-desc_detail'):
                continue
            rows = {}
            for row in section.walk():
                if row.tag != 'tr':
                    continue
                th, td = (next((n for n in row.children if getattr(n, 'tag', None) == tag), None)
                          for tag in ('th', 'td'))
                if th and td:
                    rows[th.text().strip()] = td
            if not rows.get('品番') or rows['品番'].text().strip() != code[1] or not rows.get('洗濯表記'):
                continue
            method = next((n for n in rows['洗濯表記'].walk() if n.tag == 'span'), None)
            if method:
                values.add(' '.join(method.text().split()))
        value = next(iter(values)) if len(values) == 1 else None
        care = pal_care_text(value, 'official_store_care')
        claims = title_features(name)
        phrase = re.match(r'^(?:『洗濯可』[ \t]*)?(抗ピル|UVケア)', name)
        if phrase:
            claims.update(named_features([phrase[1]]))
        return assemble_detail(name, url, care, claims) if care else None
    return None


def onward_composition(variants):
    values = set()
    for variant in variants:
        materials = set()
        for row in variant.walk():
            if not row.has_class('c-item-detail-expand-colors-detail__info'):
                continue
            labels = [' '.join(node.text().split()) for node in row.walk()
                      if node.has_class('c-item-detail-expand-colors-detail__info-material')]
            if labels == ['素材']:
                materials.update(' '.join(node.text().split()) for node in row.walk()
                                 if node.has_class('c-item-detail-expand-colors-detail__info-detail'))
        if len(materials) != 1:
            return None
        material = materials.pop()
        if not re.search(r'\d\s*[%％]', material):
            return None
        values.add(material)
    return values.pop() if len(values) == 1 else None


def onward_detail(doc, url, meta, title):
    code = re.fullmatch(r'/items/([A-Z0-9]{8,24})/?', urlsplit(url).path)
    if not code:
        return None
    for item in product_jsonld(doc, 'Product'):
        brand = item.get('brand')
        if (item.get('mpn') == code[1] and isinstance(brand, dict)
                and isinstance(brand.get('name'), str) and matches(brand['name'], meta)
                and (not meta.get('brand_code') or brand.get('brandCode') == meta['brand_code'])):
            break
    else:
        return None
    specs = [node for node in doc.root.walk() if node.has_class('c-item-description-tab__item-detail-info')]
    if len(specs) != 1:
        return None
    variants = [node for node in specs[0].walk() if node.has_class('c-item-detail-expand-colors-detail__body')]
    declarations = set()
    for variant in variants:
        icons = [re.fullmatch(r'https://crosset\.onward\.co\.jp/images/washIcons/([1-7][0-9]{2})\.svg',
                              node.attrs.get('src', ''))
                 for node in variant.walk() if node.tag == 'img'
                 and node.has_class('c-item-detail-expand-colors-detail__wash-icon')]
        if not icons or not all(icons):
            return None
        declarations.add(tuple(sorted({icon[1] for icon in icons if icon[1][0] in '16'})))
    if len(declarations) != 1:
        return None
    codes = next(iter(declarations))
    care = jis_care_text('洗濯記号 '+','.join(codes), 'onward_symbols')
    name = title.partition(' | ')[0].rpartition(' / ')[0]
    detail = assemble_detail(name, url, care, title_features(name)) if name and care else None
    if detail and (composition := onward_composition(variants)):
        detail.update(composition=composition, composition_evidence='OFFICIAL_MATCHING_PRODUCT_TABLE')
    return detail


@lru_cache(maxsize=1)
def mix_symbol_map():
    return json.loads((Path(__file__).resolve().parents[1]/MIX_CARE_CONFIG).read_bytes())


def mix_label(code):
    if not isinstance(code, str):
        return None
    mapping = mix_symbol_map()
    symbols = mapping['codes'].get(code)
    if not symbols:
        return None
    parsed = jis_care_text('洗濯記号 '+','.join(symbols), 'mix_symbols')
    return {**parsed, 'wash_code':code, 'symbol_map_sha256':mapping['sha256']} if parsed else None


def with_composition(detail, materials):
    if detail and len(materials) == 1:
        material = next(iter(materials))
        if re.search(r'\d\s*[%％]', material):
            detail.update(composition=material, composition_evidence='OFFICIAL_MATCHING_PRODUCT_TABLE')
    return detail


def mix_knit_group(group):
    category = group.get('category')
    if category in ('knit_sweater', 'cardigan'):
        return True
    name = group.get('name')
    if not isinstance(name, str):
        return False
    name = unicodedata.normalize('NFKC', name)
    if category == 'jacket':
        return 'ニットジャケット' in name
    return category in ('knit_onepiece', 'other_onepiece') and 'ニットセットアップ' in name


def mix_detail(doc, url, meta, path):
    if not re.fullmatch(r'/products/017[0-9]{7}', path):
        return None
    groups = [row for row in product_jsonld(doc,'ProductGroup') if row.get('@id') == path+'#product'
              and mix_knit_group(row) and isinstance(row.get('brand'),dict)
              and isinstance(row['brand'].get('name'),str) and matches(row['brand']['name'],meta)]
    if len(groups) != 1:
        return None
    fields = {}
    for node in doc.root.walk():
        if not node.has_class('c_detail__item'):
            continue
        title, value = (next((child for child in node.children if getattr(child,'tag',None)
                              and child.has_class(cls)), None) for cls in ('c_detail__title','c_detail__content'))
        if title and value:
            fields.setdefault(title.text().strip(), []).append(value)
    codes, washes = fields.get('商品番号', []), fields.get('洗濯表示', [])
    if len(codes) != 1 or codes[0].text().split()[:1] != [path.rsplit('/',1)[-1]] or len(washes) != 1:
        return None
    wash = washes[0]
    nodes = [node for node in wash.walk() if node.attrs.get('id') == 'wash_images']
    if len(nodes) != 1:
        return None
    references = {match for node in wash.walk() if node.tag=='script'
                  for match in re.findall(r"fetch\(\s*['\"]([^'\"]+)['\"]", ''.join(
                      child for child in node.children if isinstance(child,str)))}
    if references != {mix_symbol_map()['url']}:
        return None
    care = mix_label(nodes[0].text().strip())
    name = groups[0].get('name')
    detail = assemble_detail(name,url,care,title_features(name)) if isinstance(name,str) else None
    return with_composition(detail, {' '.join(node.text().split()) for node in fields.get('素材',[])})


def united_arrows_care(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r'ケア方法[:：]\s*(.+)', value.strip())
    if not match:
        return None
    original = match[1]
    tokens = re.split(r'\s*[/／・、]\s*', original)
    known = {label for states in TOKENS.values() for labels in states.values() for label in labels}
    if any(unicodedata.normalize('NFKC', token) not in known for token in tokens):
        return None
    care = care_from_text(original)
    return {**care, 'source_text': value, 'text_format': 'united_arrows_care'}


def united_arrows_detail(doc, url, canonical, path, meta):
    if not re.fullmatch(r'/brand/glr/item/[A-Z0-9]{12}', path):
        return None
    groups = [group for group in product_jsonld(doc, 'ProductGroup')
              if group.get('url') == canonical.geturl() and isinstance(group.get('brand'), dict)
              and group['brand'].get('name') == meta['brand_name']]
    if len(groups) != 1:
        return None
    product_codes = {match[1] for node in doc.root.walk() if node.tag == 'span'
                     and (match := re.fullmatch(r'商品番号\s+([0-9]{4}-[0-9]-[0-9]{6})', node.text()))}
    if len(product_codes) != 1:
        return None
    sections = []
    for node in doc.root.walk():
        if node.tag != 'div' or not node.has_class('text-sm') or not node.has_class('leading-normal'):
            continue
        lines = [part.strip() for part in node.children if isinstance(part, str) and part.strip()]
        delimiters = [index for index, line in enumerate(lines) if re.fullmatch(r'={8,}', line)]
        if len(delimiters) == 2:
            sections.append(lines[delimiters[0]+1:delimiters[1]])
    if len(sections) != 1:
        return None
    section = sections[0]
    declarations = [line for line in section if re.match(r'ケア方法[:：]', line)]
    features = [line for line in section if re.match(r'機能性[:：]', line)]
    care = united_arrows_care(declarations[0]) if len(declarations) == 1 else None
    claims = named_features(re.split(r'[/／・、]', features[0][4:])) if len(features) == 1 else {}
    return assemble_detail(groups[0].get('name'), url, care, claims)


def ikka_detail(doc, url, brand, path, canonical, title):
    code = re.fullmatch(r'/c/ikka/(?:ikkaladies/ikkalknit/)?([0-9]{8})', path)
    if (not code or canonical.path.rstrip('/') != '/c/ikka/'+code[1]
            or ',ikka| TOKYO DESIGN CHANNEL' not in title or brand != 'ikka'
            or texts_from_pair(doc,'商品コード','dt','dd','dl') != {code[1]}):
        return None
    labels = texts_from_pair(doc,'クリーニング方法','dt','dd','dl')
    care = pal_care_text(next(iter(labels)), 'official_store_care') if len(labels)==1 else None
    name = title.split(',ikka|',1)[0]
    detail = assemble_detail(name,url,care,title_features(name)) if care else None
    return with_composition(detail, texts_from_pair(doc,'素材','dt','dd','dl'))


def detail_adapter(meta):
    adapter = meta.get('adapter')
    if adapter in {'onward-listing', 'onward'} or (not adapter and any(
            urlsplit(url).netloc == ONWARD_HOST for url in meta.get('entry_urls', []))):
        return 'onward'
    if not adapter and meta.get('brand_name') == 'SENSE OF PLACE':
        return 'urbanresearch'
    if adapter == 'shopify' and meta.get('brand_name') == 'NATURAL BEAUTY BASIC':
        return 'mix_care'
    return adapter


def read_care_detail(doc, url, meta, *, read_care_image_sha=None):
    """Only use known official product paths and page-level identity evidence."""
    adapter = detail_adapter(meta)
    hosts = {'fr': {'www.uniqlo.com': 'UNIQLO', 'www.gu-global.com': 'GU'},
             'doclasse': {'www.doclasse.com': 'DoCLASSE'}, 'canshop': {'www.canshop.jp': 'Te chichi'},
             'pal': {'www.palcloset.jp': meta.get('brand_name')},
             'stripe': {'stripe-club.com': meta.get('brand_name')},
             'baycrews': {'baycrews.jp': meta.get('brand_name')},
             'urbanresearch': {'www.urban-research.jp': meta.get('brand_name')},
             'mix_care': {'mix.tokyo': 'NATURAL BEAUTY BASIC'},
             'unitedarrows': {UNITED_ARROWS_HOST: 'green label relaxing'},
             'ikka': {'tokyodesignchannel.com': 'ikka'},
             'usagi': {USAGI_HOST: meta.get('brand_name')},
             'onward': {ONWARD_HOST: meta.get('brand_name')}}
    host_map = hosts.get(adapter)
    if not host_map:
        return None
    p = urlsplit(url)
    brand = host_map.get(p.hostname)
    if p.scheme != 'https' or p.username or p.password or p.port or not brand or brand != meta.get('brand_name'):
        return None
    if p.query and (adapter != 'unitedarrows' or any(
            len(values) != 1 or key not in UNITED_ARROWS_VARIANT_QUERY
            or not re.fullmatch(UNITED_ARROWS_VARIANT_QUERY[key], values[0])
            for key, values in parse_qs(p.query, keep_blank_values=True).items())):
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
    care = None
    text = None
    title = next((n.attrs.get('content', '') for n in doc.root.walk()
                  if n.tag == 'meta' and n.attrs.get('property') == 'og:title'), '')
    if adapter == 'usagi' and canonical.path.rstrip('/') == path:
        title = next((n.text().strip() for n in doc.root.walk() if n.tag == 'title'), title)
        return usagi_detail(doc, url, meta, path, title, read_care_image_sha)
    if adapter == 'fr' and canonical.path.rstrip('/') == path:
        token = re.fullmatch(r'/jp/ja/products/(E[0-9]{6}-[0-9]{3})/([0-9]{2})', path)
        if not token:
            return None
        name, text, claims = get_fr_care(doc, *token.groups())
        care = fr_washing_field(text)
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
    elif adapter == 'pal' and canonical.path.rstrip('/') == path:
        token = re.fullmatch(r'/display/item/([A-Z0-9]{10,24})', path)
        if not token:
            return None
        name, care, claims = pal_detail(doc, token[1], meta)
    elif adapter == 'stripe' and canonical.path.rstrip('/') == path:
        return stripe_detail(doc, url, meta['slug'])
    elif adapter == 'baycrews' and canonical.path.rstrip('/') == path:
        code = path.rsplit('/', 1)[-1]
        if not re.fullmatch(r'[0-9]{14}', code):
            return None
        name, care = baycrews_detail(doc, code, meta['slug'], path, title, meta)
    elif adapter == 'urbanresearch' and canonical.path.rstrip('/') == path:
        return urban_detail(doc, url, meta)
    elif adapter == 'onward' and canonical.path.rstrip('/') == path:
        return onward_detail(doc, url, meta, title)
    elif adapter == 'mix_care' and canonical.path.rstrip('/') == path:
        return mix_detail(doc, url, meta, path)
    elif adapter == 'unitedarrows' and canonical.path == path:
        return united_arrows_detail(doc, url, canonical, path, meta)
    elif adapter == 'ikka':
        return ikka_detail(doc, url, brand, path, canonical, title)
    else:
        return None
    return assemble_detail(name, url, care or care_from_text(text), claims)


def assemble_detail(name, url, care, claims):
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
