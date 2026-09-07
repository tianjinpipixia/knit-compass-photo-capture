"""Official storefront adapters; scope and price come from the returned source.

No AI inference, paid endpoint, or browser automation. Adapters return only cards
whose brand/women/knit scope can be supported by fields or selected category URL.
"""
import json
import re
from urllib.parse import urlsplit, urljoin, urlunsplit, parse_qs
import unicodedata

KNIT = re.compile(r'ニット|セーター|カーディガン|編み|knit|cardigan|sweater', re.I)
OTHER = re.compile(r'キッズ|メンズ|\bKIDS\b|\bMEN\b|ニット帽|キャップ|ストール|バッグ|スカート|ワンピース|パンツ', re.I)

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


def extract(doc,source,meta):
    adapter=meta.get('adapter'); items={}
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
            brand=text(cls(n,'brand'));name=text(cls(n,'title'))
            if not matches(brand,meta) or not knit(name):continue
            # Gender code 001 is the official レディース filter.
            if parse_qs(urlsplit(source).query).get('sex')!=['001']:continue
            url=urljoin(source,n.attrs['href']);amount=price(text(cls(n,'price')));status=labels(cls(n,'ico_box'))
        elif adapter=='dot':
            if n.tag!='a' or not re.search(r'^/'+re.escape(meta['slug'])+r'/disp/item/\d+/',n.attrs.get('href','')):continue
            if parse_qs(urlsplit(source).query).get('dispNo')!=['001001']:continue
            name=text(cls(n,'item-name'))
            if not knit(name):continue
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
            # Brand-specific women's labels (not the shared shopping site header).
            if not any(norm(x) in norm(name) for x in [meta['brand_name']]+meta.get('brand_aliases',[])):continue
            url=urljoin(source,n.attrs['href'])
            card=parent_with(n,lambda p:p.tag=='li',4)
            amount=price(text(card) if card else name);status=labels(card) if card else []
            name=name.split('¥')[0].strip()
        elif adapter=='ikka':
            if not n.has_class('fs-c-productListItem'):continue
            if '/ikkaladies/ikkalknit/' not in source:continue
            a=next((a for a in n.walk() if a.tag=='a' and re.search(r'/c/ikka/\d+$',a.attrs.get('href',''))),None)
            if not a:continue
            name=text(cls(n,'fs-c-productName__name'))
            if not name or OTHER.search(name):continue
            url=urljoin(source,a.attrs['href']);amount=price(text(cls(n,'fs-c-productPrice')));status=labels(cls(n,'fs-c-productMarks'))
        else:continue
        if not url or not name or not amount or OTHER.search(name):continue
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
