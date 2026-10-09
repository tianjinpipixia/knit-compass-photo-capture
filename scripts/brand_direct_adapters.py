"""Official storefront adapters; scope and price come from the returned source.

No AI inference, paid endpoint, or browser automation. Adapters return only cards
whose brand/women/knit scope can be supported by fields or selected category URL.
"""
import json
import re
from urllib.parse import urlsplit, urljoin, urlunsplit, parse_qs
import unicodedata

KNIT = re.compile(r'ニット|セーター|カーディガン|編み|knit|cardigan|sweater', re.I)
OTHER = re.compile(r'キッズ|メンズ|ユニセックス|\bKIDS\b|\bMEN\b|\bUNISEX\b|ニット帽|ビーニー|ワッチ|シュシュ|キャップ|ストール|バッグ|スカート|ワンピース|パンツ', re.I)

def text(n): return re.sub(r'\s+', ' ', n.text()).strip() if n else ''
def norm(t): return re.sub(r'[^\w]', '', unicodedata.normalize('NFKD',t).casefold())
def matches(t, meta): return norm(t) in {norm(x) for x in [meta['brand_name']]+meta.get('brand_aliases',[])}
def cls(n, name): return n.cls(name)
def price(t):
    found=re.findall(r'[¥￥]\s*[\d,]+|[\d,]+\s*円',t)
    return ' / '.join(dict.fromkeys(found))
def labels(n):
    s=text(n)
    return [x for x in ['NEW','予約','再入荷','SALE','WEB限定','新作'] if x.lower() in s.lower()]
def canonical(url):
    # These storefront product identities are in the path. Variants stay in evidence.
    p=urlsplit(url);return urlunsplit((p.scheme,p.netloc,p.path,'',''))
def record(name,url,amount,status,source,code='',evidence='OFFICIAL_LISTING_CARD'):
    return {'product_name':name,'product_url':canonical(url),'product_code':code,
            'display_price':amount,'status_labels':status,'source_url':source,
            'evidence_level':evidence,'scope_status':'BRAND_AND_KNIT_PATH_MATCHED'}
def knit(name):return bool(KNIT.search(name)) and not OTHER.search(name)
def excluded_by_meta_scope(name,meta):
    if not meta.get('normal_line_only'):return False
    folded=unicodedata.normalize('NFKC',name).casefold()
    return any(unicodedata.normalize('NFKC',marker).casefold() in folded
               for marker in meta.get('excluded_name_markers',[]))
def parent_with(n, predicate, max_depth=5):
    for _ in range(max_depth):
        if predicate(n):return n
        n=n.parent
        if n is None:break
    return None


def fr_state(doc,source,meta):
    result={}
    # Hydration includes unrelated recommendations. Require an explicit women's
    # product field plus knit name; never count every object on a women's page.
    for n in doc.root.walk():
        if n.tag!='script':continue
        body=''.join(x for x in n.children if isinstance(x,str))
        if 'window.__PRELOADED_STATE__' not in body:continue
        try:state=json.JSONDecoder().raw_decode(body.split('window.__PRELOADED_STATE__',1)[1].split('=',1)[1].lstrip())[0]
        except (ValueError,IndexError):continue
        entities=state.get('entity',{}).get('searchEntity',{})
        for entity in entities.values():
            p=entity.get('product',{})
            if p.get('genderCategory')!='WOMEN' and p.get('sizeGender')!='WOMEN':continue
            name=p.get('name','')
            if not knit(name):continue
            pid=p.get('productId','');group=p.get('priceGroup','')
            if not re.fullmatch(r'E\d+-\d+',pid) or not re.fullmatch(r'\d+',str(group)):continue
            url=urljoin(source,f'/jp/ja/products/{pid}/{group}')
            prices=p.get('prices',{}); pr=prices.get('promo') or prices.get('base') or {}
            if pr.get('currency',{}).get('code')!='JPY':continue
            flags=p.get('representative',{}).get('flags',{})
            status=[x['name'] for v in flags.values() if isinstance(v,list) for x in v if isinstance(x,dict) and x.get('name')]
            result[url]=record(name,url,'¥'+str(pr.get('value','')),status,source,pid,'OFFICIAL_PAGE_HYDRATION')
    # Some current pages have semantic product links rather than hydration.
    for n in doc.root.walk():
        if n.tag!='a' or not re.search(r'/jp/ja/products/E\d+-\d+/\d+',n.attrs.get('href','')):continue
        s=text(n)
        if not knit(s) or not re.search(r'\bWOMEN\b',s):continue
        url=urljoin(source,n.attrs['href'])
        if urlsplit(url).hostname!=urlsplit(source).hostname:continue
        if url not in result and price(s):result[url]=record(s.split('¥')[0].strip(),url,price(s),labels(n),source)
    return list(result.values())


def doclasse_items(doc, source, meta):
    """Read only women's knit/category cards, never homepage recommendations."""
    parsed = urlsplit(source)
    params = parse_qs(parsed.query)
    category_source=(parsed.path == '/item' and params.get('brand_id') == ['1'] and
                     params.get('category_id') in (['11'], ['12']))
    new_source=(parsed.path == '/ladies/feature/newarrival' and not parsed.query)
    if (parsed.scheme != 'https' or parsed.hostname != 'www.doclasse.com' or
            not matches('DoCLASSE', meta) or not (category_source or new_source)):
        return []
    items = {}
    for card in doc.root.walk():
        if not card.has_class('item_archive__list'): continue
        if card.attrs.get('data-ga_ec_goods_brand') != 'レディース': continue
        category = card.attrs.get('data-ga_ec_goods_category', '')
        if not KNIT.search(category) or OTHER.search(category): continue
        name_node = cls(card, 'goodsNameWrapper')
        link = next((n for n in name_node.walk() if n.tag == 'a' and
                     n.has_class('goodsDetailLink')), None) if name_node else None
        if not link: continue
        name = text(link)
        if not name or OTHER.search(name): continue
        url = urljoin(source, link.attrs.get('href', ''))
        target = urlsplit(url)
        match = re.fullmatch(r'/item/detail/1_1_(\d+)/(\d+)', target.path)
        if (target.scheme != 'https' or target.hostname != parsed.hostname or
                not match or match[1] != card.attrs.get('data-ga_ec_goods_id')):
            continue
        amount = price(text(cls(card, 'price')))
        if not amount: continue
        # Colour paths stay in evidence; one displayed card per common goods ID.
        items.setdefault(match[1], record(name, url, amount,
                         labels(cls(card, 'iconList')), source, match[1]))
    return list(items.values())


def onward_listing_items(doc, source, meta):
    p = urlsplit(source); q = parse_qs(p.query)
    if (p.scheme != 'https' or p.hostname != 'crosset.onward.co.jp' or
            p.path != '/items' or q.get('bc') != [meta.get('brand_code')] or
            meta.get('brand_code') not in {'002', '003'} or
            q.get('gc') != ['2'] or q.get('du') != ['2'] or
            q.get('scc') not in (['1004'], ['1005'])):
        return []
    items = {}
    for card in doc.root.walk():
        if not card.has_class('c-item-card'): continue
        if not matches(text(cls(card, 'c-item-card__brand')), meta): continue
        try: tracking = json.loads(card.attrs.get('data-web-tracking-item', ''))
        except (ValueError, TypeError): continue
        if not isinstance(tracking, dict): continue
        if (tracking.get('brandCode') != meta['brand_code'] or
                tracking.get('smallCategoryCode') != q['scc'][0] or
                tracking.get('genderCode') not in ('', '2')): continue
        link = cls(card, 'c-item-card__name-link')
        if not link: continue
        name = text(link)
        if not name or OTHER.search(name): continue
        url = urljoin(source, link.attrs.get('href', '')); target = urlsplit(url)
        match = re.fullmatch(r'/items/([A-Za-z0-9]+)', target.path)
        if (target.scheme != 'https' or target.hostname != p.hostname or
                not match or match[1] != tracking.get('code')): continue
        amount = price(text(cls(card, 'c-item-card__price')))
        if not amount: continue
        item = record(name, url, amount, labels(cls(card, 'c-item-card__badge-upper')), source, match[1])
        items[item['product_url']] = item
    return list(items.values())


def extract(doc,source,meta):
    adapter=meta.get('adapter')
    if adapter == 'doclasse': return doclasse_items(doc, source, meta)
    if adapter == 'onward-listing': return onward_listing_items(doc, source, meta)
    # SENSE OF PLACE currently renders useful official listing cards on its
    # brand page without a configured adapter. Keep this narrow to that exact
    # first-party host/brand rather than treating all generic links as verified.
    if not adapter and urlsplit(source).hostname=='www.urban-research.jp' and meta.get('brand_name')=='SENSE OF PLACE':
        adapter='urbanresearch'
    items={}
    if adapter=='fr':return fr_state(doc,source,meta)
    for n in doc.root.walk():
        name=brand=amount=code='';url='';status=[]
        if adapter=='usagi':
            if not n.has_class('m-item'):continue
            brand=text(cls(n,'m-item-brand'));name=text(cls(n,'m-item-name'))
            category=text(cls(n,'m-item-category'))
            if not matches(brand,meta) or not knit(category):continue
            a=next((a for a in n.walk() if a.tag=='a' and '/brand/'+meta['slug']+'/item/' in a.attrs.get('href','')),None)
            if not a:continue
            url=urljoin(source,a.attrs['href']);amount=price(text(cls(n,'m-item-price')));status=labels(cls(n,'m-item-icon'))
        elif adapter=='pal':
            if n.tag!='a' or '/display/item/' not in n.attrs.get('href',''):continue
            brand=text(cls(n,'brand')) or next((text(p) for p in n.walk() if p.tag=='p' and matches(text(p),meta)), '')
            name=text(cls(n,'title')) or text(cls(n,'textOverflow'))
            if not matches(brand,meta) or not knit(name):continue
            # Gender code 001 is the official レディース filter.
            if parse_qs(urlsplit(source).query).get('sex')!=['001']:continue
            url=urljoin(source,n.attrs['href']);amount=price(text(cls(n,'price')));status=labels(cls(n,'ico_box'))
        elif adapter=='dot':
            if n.tag!='a' or not re.search(r'^/'+re.escape(meta['slug'])+r'/disp/item/\d+/',n.attrs.get('href','')):continue
            if parse_qs(urlsplit(source).query).get('dispNo')!=['001001']:continue
            name=text(cls(n,'item-name'))
            if not knit(name) or excluded_by_meta_scope(name,meta):continue
            url=urljoin(source,n.attrs['href']);amount=price(text(cls(n,'item-price')));status=labels(cls(n,'item-icon'))
        elif adapter=='shopify':
            if not n.has_class('product-item-meta'):continue
            name=text(cls(n,'product-item-meta__title'));brand=text(cls(n,'product-item-meta__vendor'))
            if not matches(brand,meta) or not knit(name):continue
            a=cls(n,'product-item-meta__title')
            if not a or not a.attrs.get('href','').startswith('/products/'):continue
            url=urljoin(source,a.attrs['href']);amount=price(text(cls(n,'price-list')))
            status=labels(cls(n,'label-list')) # hidden "sale price" accessibility copy is not a sale badge.
        elif adapter=='muji':
            if n.tag!='a' or not re.search(r'/cmdty/detail/\d+',n.attrs.get('href','')):continue
            name=text(n)
            if not name.startswith('婦人') or not knit(name):continue
            card=parent_with(n,lambda p:'__container' in p.attrs.get('class','') and p.tag=='div',3)
            if not card:continue
            url=urljoin(source,n.attrs['href']);amount=price(text(card));status=labels(card)
        elif adapter=='world':
            if not n.has_class('block_item'):continue
            a=next((a for a in n.walk() if a.tag=='a' and re.search(r'/brand/'+re.escape(meta['slug'])+r'/item/[^/?]+',a.attrs.get('href',''))),None)
            if not a:continue
            # Exact brand field and women's category entry are required.
            if not meta.get('women_category_entry'):continue
            s=text(a)
            if not knit(s) or norm(meta['brand_name']) not in norm(s):continue
            url=urljoin(source,a.attrs['href']);name=s.split('¥')[0].strip();amount=price(s);status=labels(n)
        elif adapter=='stripe':
            if n.tag!='a' or '/brand/'+meta['slug']+'/item/' not in n.attrs.get('href',''):continue
            name=text(n)
            if not knit(name) or len(name)>350:continue
            # The current brand-specific Stripe cards do not always render a
            # visible price. Brand + item path + card text still establish the
            # product identity/scope; retain blank price for later enrichment.
            if '/brand/'+meta['slug']+'/' not in urlsplit(source).path:continue
            if not any(norm(x) in norm(name) for x in [meta['brand_name']]+meta.get('brand_aliases',[])):continue
            url=urljoin(source,n.attrs['href'])
            card=parent_with(n,lambda p:p.tag=='li',4)
            amount=price(text(card) if card else name);status=labels(card) if card else []
            name=name.split('¥')[0].strip()
        elif adapter=='unitedarrows':
            params=parse_qs(urlsplit(source).query)
            if params.get('lm')!=['10W1'] or params.get('ca') not in (['0105'],['0108']):continue
            if n.tag!='a' or not re.search(r'^/brand/glr/item/[A-Za-z0-9]+',n.attrs.get('href','')):continue
            s=text(n)
            if not matches('green label relaxing',meta) or not knit(s) or not price(s):continue
            url=urljoin(source,n.attrs['href']);name=s.split('¥')[0].strip();amount=price(s);status=labels(n)
        elif adapter=='onward':
            if parse_qs(urlsplit(source).query).get('du')!=['2']:continue
            if n.tag!='a' or not re.search(r'^/items/[A-Za-z0-9]+',n.attrs.get('href','')):continue
            s=text(n)
            if not s.startswith(meta['brand_name']+' ') or not knit(s) or not price(s):continue
            url=urljoin(source,n.attrs['href']);name=s.split('¥')[0].replace(meta['brand_name'],'',1).strip();amount=price(s);status=labels(n)
        elif adapter=='baycrews':
            params=parse_qs(urlsplit(source).query)
            selected_query=(urlsplit(source).path=='/item/list' and
                            params.get('q_mtype')==['1'] and
                            params.get('q_mshop')==[meta.get('shop_code')])
            selected_path=(urlsplit(source).path==f"/item/list/{meta['slug']}/category/cutsew/ladys" and
                           params.get('q_mtype',['1'])==['1'] and
                           params.get('q_mshop',[meta.get('shop_code')])==[meta.get('shop_code')])
            if not (selected_query or selected_path) or params.get('q_mccate') not in (['231'],['223']):continue
            if n.tag!='a' or not n.attrs.get('href'):continue
            candidate=urljoin(source,n.attrs['href']); parsed=urlsplit(candidate)
            if parsed.scheme!='https' or parsed.hostname!=urlsplit(source).hostname:continue
            if not re.fullmatch(r'/item/detail/'+re.escape(meta['slug'])+r'/[^/]+/[0-9]+/?',parsed.path):continue
            # Bound fields to one product card. A list ancestor contains prices
            # and brands from neighbours and cannot establish this item's scope.
            card=parent_with(n,lambda p:p.tag=='li' and p.has_class('item'),6)
            if not card:continue
            brand=text(cls(card,'brand'));name=text(cls(card,'itemName'))
            if not matches(brand,meta) or not name:continue
            url=candidate;amount=price(text(cls(card,'price')))
            status=labels(cls(card,'status'))
        elif adapter=='urbanresearch':
            if not n.has_class('block-thumbnail-t--goods'):continue
            brand=text(cls(n,'block-thumbnail-t--goods-label'))
            name=text(cls(n,'block-thumbnail-t--goods-name'))
            if not matches(brand,meta) or not knit(name):continue
            a=next((a for a in n.walk() if a.tag=='a' and re.search(r'^/shop/g/g[A-Za-z0-9-]+/',a.attrs.get('href',''))),None)
            if not a:continue
            url=urljoin(source,a.attrs['href'])
            amount=price(text(cls(n,'block-thumbnail-t--price-infos')) or text(n));status=labels(n)
        elif adapter=='ikka':
            if not n.has_class('fs-c-productListItem'):continue
            if '/ikkaladies/ikkalknit/' not in source:continue
            a=next((a for a in n.walk() if a.tag=='a' and re.search(r'/c/ikka/(?:ikkaladies/ikkalknit/)?\d+/?$',a.attrs.get('href',''))),None)
            if not a:continue
            name=text(cls(n,'fs-c-productName__name'))
            if not name or OTHER.search(name):continue
            url=urljoin(source,a.attrs['href']);amount=price(text(cls(n,'fs-c-productPrice')));status=labels(cls(n,'fs-c-productMarks'))
        else:continue
        if not url or not name or (not amount and adapter not in {'stripe'} ) or OTHER.search(name):continue
        if urlsplit(url).hostname!=urlsplit(source).hostname:continue
        url=canonical(url);code=urlsplit(url).path.rstrip('/').split('/')[-1]
        items[url]=record(name,url,amount,status,source,code)
    return list(items.values())


def extract_json(body,source,meta):
    if meta.get('adapter')!='canshop':return []
    data=json.loads(body);items=[]
    for p in data.get('response',{}).get('docs',[]):
        if p.get('bd')!='CAN02' or not matches(p.get('bdName',''),meta):continue
        name=p.get('name','')
        if not knit(name) and not knit(p.get('mcn2','')+' '+p.get('mcn3','')):continue
        if OTHER.search(name):continue
        code=p.get('cd','')
        if not re.fullmatch(r'[A-Za-z0-9]+',code):continue
        url='https://www.canshop.jp/ap/item/i/'+code
        item=record(name,url,'¥'+str(p.get('price','')),p.get('icon',[]),source,code,'OFFICIAL_STOREFRONT_JSON')
        item['composition']=' / '.join(p.get('material') or [])
        item['official_product_codes']=p.get('mkcode') or []
        items.append(item)
    return items
