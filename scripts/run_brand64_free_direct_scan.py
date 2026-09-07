#!/usr/bin/env python3
"""No-key, no-AI-API official source collector. Observations are review candidates.

A fetched page is never proof of exhaustive brand coverage. Unavailable/unsupported
pages stay in the unresolved queue; old products are never deleted on absence.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import gzip
import hashlib
from html.parser import HTMLParser
import json
import pathlib
import re
import threading
import time
import unicodedata
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'data/brand-md-monitoring/direct-scans'
UA = 'KnitCompassOfficialMonitor/1.0'
OFFICIAL_HOSTS = {urlsplit(u).hostname for meta in json.loads((ROOT/'config/brand64-free-direct-sources.json').read_text())['brands'].values() for u in meta.get('entry_urls',[]) + meta.get('watch_product_urls',[])}
MAX_BYTES = 4_000_000
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

class Node:
    def __init__(self, tag='', attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []
    def walk(self):
        yield self
        for x in self.children:
            if isinstance(x, Node): yield from x.walk()
    def text(self):
        if self.tag in {'script','style','noscript'}: return ''
        return ' '.join(x.text() if isinstance(x, Node) else x for x in self.children).strip()
    def has_class(self, name): return name in self.attrs.get('class','').split()
    def cls(self, name): return next((n for n in self.walk() if n.has_class(name)), None)

class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node(); self.current = self.root
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.current); self.current.children.append(n)
        if tag not in VOID: self.current = n
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID: self.handle_endtag(tag)
    def handle_endtag(self, tag):
        n = self.current
        while n.parent:
            if n.tag == tag: self.current = n.parent; return
            n = n.parent
    def handle_data(self, data): self.current.children.append(data)


def clean(text): return re.sub(r'\s+', ' ', str(text or '')).strip()
def norm(text): return re.sub(r'[^\w]', '', unicodedata.normalize('NFKD', text).casefold())
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def today(): return dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date().isoformat()
def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def canonical(url):
    p = urlsplit(url)
    # Preserve product identity in query parameters; only remove known tracking/color variants.
    q = [(k,v) for k,v in parse_qsl(p.query) if not k.startswith('utm_') and k not in {'cc','color','srsltid'}]
    return urlunsplit((p.scheme,p.netloc,p.path,urlencode(q),''))
def public_url(url):
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError('Only public HTTPS sources are supported')
    if p.hostname not in OFFICIAL_HOSTS:
        raise ValueError('Redirect/source host is not in the configured official source allowlist')

class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

class Fetcher:
    def __init__(self, evidence_root):
        self.root = evidence_root
        self.guard = threading.Lock(); self.locks = {}; self.last = {}; self.count = 0
    def __call__(self, url):
        public_url(url)
        host = urlsplit(url).hostname
        with self.guard: lock = self.locks.setdefault(host,threading.Lock())
        with lock:
            time.sleep(max(0,1.5-(time.monotonic()-self.last.get(host,0))))
            self.last[host] = time.monotonic()
            with self.guard: self.count += 1
            req = urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'text/html'})
            with urllib.request.build_opener(SafeRedirect()).open(req,timeout=15) as r:
                data = r.read(MAX_BYTES+1)
                if len(data)>MAX_BYTES: raise ValueError('Source exceeds size limit')
                if 'html' not in r.headers.get('Content-Type',''): raise ValueError('Not an HTML source')
                html = data.decode(r.headers.get_content_charset() or 'utf-8',errors='replace')
                final_url = r.url
        sha = hashlib.sha256(data).hexdigest()
        path = self.root / (sha+'.html.gz'); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(gzip.compress(data,mtime=0))
        return html, {'requested_url':url,'url':final_url,'retrieved_at_utc':now(),'sha256':sha,'evidence_path':str(path)}


def jun_items(doc, source, meta):
    items = {}
    pattern = re.compile(r'^/'+re.escape(meta['slug'])+r'/product/tops/(?:knit-sweater|cardigan)/([^/]+)$')
    for n in doc.root.walk():
        if not n.has_class('content-cassette'): continue
        link = next((a.attrs.get('href') for a in n.walk() if a.tag=='a' and a.has_class('content-cassette__link')),None)
        if not link: continue
        url = canonical(urljoin(source,link)); match = pattern.match(urlsplit(url).path)
        if not match or urlsplit(url).hostname!=urlsplit(source).hostname: continue
        name = n.cls('item-name'); brand = n.cls('brand-name'); price = n.cls('item-price'); tags = n.cls('item-tag')
        if name is None or brand is None or norm(clean(brand.text())) != norm(meta['brand_name']): continue
        if re.search(r'KIDS|キッズ|メンズ', name.text(), re.I): continue
        items[url] = {'product_name':clean(name.text()),'product_code':match[1], 'product_url':url,
            'display_price':clean(price.text()) if price else '',
            'status_labels':[clean(x.text()) for x in tags.walk() if x.tag=='span' and clean(x.text())] if tags else [],
            'evidence_level':'OFFICIAL_LISTING_CARD','scope_status':'BRAND_AND_KNIT_PATH_MATCHED',
            'source_url':source}
    return list(items.values())


def generic_items(doc, source, meta):
    # Conservative discovery only: a brand home page may link other brands/men.
    # These links require scope verification and do not count as confirmed products.
    items = {}
    for a in doc.root.walk():
        if a.tag!='a' or not a.attrs.get('href'): continue
        url = canonical(urljoin(source,a.attrs['href']))
        if urlsplit(url).hostname != urlsplit(source).hostname: continue
        if not re.search(r'/products?/|/item/|/goods/|/commodity/', url): continue
        text = clean(a.text()) or clean(' '.join(n.attrs.get('alt','') for n in a.walk() if n.tag=='img'))
        if not re.search(r'ニット|セーター|カーディガン|knit|cardigan',text,re.I): continue
        if re.search(r'KIDS|キッズ|メンズ|MEN\b',text,re.I): continue
        if len(text)>500 or not text: continue
        items[url]={'product_name':text,'product_url':url,'display_price':'','status_labels':[],
                    'evidence_level':'OFFICIAL_PAGE_LINK','scope_status':'BRAND_AND_GENDER_REVIEW_REQUIRED','source_url':source}
    return list(items.values())


def product_detail(html, url, meta):
    doc = Document(html)
    def objects(obj):
        if isinstance(obj,dict):
            yield obj
            for v in obj.values(): yield from objects(v)
        elif isinstance(obj,list):
            for v in obj: yield from objects(v)
    for n in doc.root.walk():
        if n.tag!='script' or n.attrs.get('type')!='application/ld+json': continue
        try: data=json.loads(''.join(x for x in n.children if isinstance(x,str)))
        except (ValueError,TypeError): continue
        for obj in objects(data):
            if obj.get('@type')!='Product': continue
            brand=obj.get('brand') or {}; brand=brand.get('name','') if isinstance(brand,dict) else str(brand)
            if norm(brand)!=norm(meta['brand_name']): continue
            offers=obj.get('offers') or []; offers=offers if isinstance(offers,list) else [offers]
            offers=[o for o in offers if isinstance(o,dict) and canonical(o.get('url',''))==canonical(url)]
            if not offers: continue
            result={'product_name':clean(obj.get('name')), 'product_url':canonical(url),
                    'description':clean(obj.get('description')), 'offers':offers,
                    'evidence_level':'OFFICIAL_PRODUCT_JSONLD','source_url':url}
            for row in doc.root.walk():
                if row.tag!='tr':continue
                th=next((x for x in row.walk() if x.tag=='th'),None);td=next((x for x in row.walk() if x.tag=='td'),None)
                if th and td and clean(th.text())=='素材':result['composition']=clean(td.text())
            return result
    raise ValueError('No matching official product JSON-LD found')


def scan_brand(bid,meta,fetch):
    row={'brand_id':bid,'brand_name':meta['brand_name'],'collector':'DIRECT_HTTP_NO_AI_API',
         'scan_status':'UNRESOLVED','coverage_status':'PARTIAL_NOT_EXHAUSTIVE',
         'sources':[],'errors':[],'surface_items':[],'product_details':[]}
    unique={}
    for url in meta.get('entry_urls',[])[:2]:
        try:
            html,evidence=fetch(url); row['sources'].append(evidence)
            doc=Document(html)
            items=jun_items(doc,evidence['url'],meta) if meta.get('adapter')=='jun' else generic_items(doc,evidence['url'],meta)
            for item in items:
                item['source_sha256']=evidence['sha256'];unique[item['product_url']]=item
            if not items:row['errors'].append({'url':url,'reason':'NO_SUPPORTED_PRODUCT_CARDS_OR_DYNAMIC_PAGE'})
        except (OSError,ValueError,TimeoutError) as exc:
            row['errors'].append({'url':url,'reason':type(exc).__name__+': '+str(exc)[:300]})
    row['surface_items']=list(unique.values())
    for url in meta.get('watch_product_urls',[])[:2]:
        try:
            html,evidence=fetch(url);row['sources'].append(evidence)
            detail=product_detail(html,evidence['url'],meta);detail['source_sha256']=evidence['sha256']
            detail['discovered_in_listing']=canonical(url) in unique
            row['product_details'].append(detail)
        except (OSError,ValueError,TimeoutError) as exc:
            row['errors'].append({'url':url,'reason':type(exc).__name__+': '+str(exc)[:300]})
    if unique:row['scan_status']='PRODUCTS_OBSERVED' if meta.get('adapter')=='jun' else 'LINK_CANDIDATES_OBSERVED'
    elif row['product_details']:row['scan_status']='WATCH_PRODUCT_ONLY'
    elif row['sources']:row['scan_status']='SOURCE_OBSERVED_EXTRACTION_PENDING'
    row['next_action']='Verify remaining listing pages, new/preorder/sale surfaces and unresolved sources; never infer no-change.'
    return row


def update_baseline(rows, known, date):
    known=json.loads(json.dumps(known)); changes=[]
    for row in rows:
        for item in row['surface_items']:
            if item.get('scope_status')!='BRAND_AND_KNIT_PATH_MATCHED': continue
            key=row['brand_id']+'|'+item['product_url']; before=known.get(key)
            record={**item,'brand_id':row['brand_id'],'brand_name':row['brand_name'],
                    'first_seen_date':before['first_seen_date'] if before else date,'last_seen_date':date,
                    'sales_start_date':None,'publication_status':'PUBLISH_HOLD','human_review_required':True}
            if before is None:
                changes.append({**record,'delta_type':'FIRST_OBSERVED_CANDIDATE','is_new_release_confirmed':False})
            elif any(before.get(k)!=item.get(k) for k in ('display_price','status_labels','product_name')):
                changes.append({**record,'delta_type':'OBSERVED_FIELD_CHANGE','previous_values':{k:before.get(k) for k in ('display_price','status_labels','product_name')}})
            known[key]=record
    return known,changes


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--brand',action='append');ap.add_argument('--output-root',default=str(OUT));ap.add_argument('--date',default=today())
    args=ap.parse_args()
    if args.date!=today():ap.error('Live observations cannot be backdated')
    out=pathlib.Path(args.output_root)
    config=json.loads((ROOT/'config/brand64-free-direct-sources.json').read_text())
    active=json.loads((ROOT/'config/brand64-active-brands.json').read_text())['active_brands']
    if args.brand and any(b not in active for b in args.brand):ap.error('Unknown brand')
    selected=[b for b in active if not args.brand or b in args.brand]
    # Known issue first, followed by configured Tier A brands, then remaining active brands.
    tier=json.loads((ROOT/'config/brand64-md-monitoring.json').read_text())['tiered_analysis']['tier_a_deep_dive_brand_ids']
    selected.sort(key=lambda b:(b!='BR-00004',b not in tier,list(active).index(b)))
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    fetch=Fetcher(out/args.date/stamp/'evidence')
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows=list(pool.map(lambda bid:scan_brand(bid,config['brands'].get(bid,{'brand_name':active[bid]}),fetch),selected))
    baseline_path=out/'known-products.json'
    known=json.loads(baseline_path.read_text()) if baseline_path.exists() else {}
    known,changes=update_baseline(rows,known,args.date);save(baseline_path,known)
    product_brands=[r['brand_id'] for r in rows if r['scan_status']=='PRODUCTS_OBSERVED']
    summary={'format':'KC_BRAND64_FREE_DIRECT_SCAN','schema_version':'1.0','observed_date':args.date,'generated_at_utc':now(),
        'collector':'DIRECT_HTTP_NO_AI_API','ai_api_request_count':0,'billing_enabled_by_this_job':False,
        'active_brand_count':len(active),'attempted_brand_count':len(rows),'http_request_count':fetch.count,
        'product_observed_brand_count':len(product_brands),
        'product_count':sum(len(r['surface_items']) for r in rows if r['scan_status']=='PRODUCTS_OBSERVED'),
        'unverified_link_candidate_count':sum(len(r['surface_items']) for r in rows if r['scan_status']=='LINK_CANDIDATES_OBSERVED'),
        'candidate_delta_count':len(changes),'required_product_observed_brand_count':39,
        'scan_status':'PARTIAL_COVERAGE','exhaustive_brand_count':0,
        'unresolved_brand_ids':[r['brand_id'] for r in rows if r['scan_status']!='PRODUCTS_OBSERVED'],
        'not_attempted_brand_ids':[b for b in active if b not in selected],
        'coverage_rule':'Entry-page observation only; no claim of exhaustive coverage or no-change. First observed is not launch date.',
        'publication_status':'PUBLISH_HOLD','human_review_required':True,'sales_quantity_estimation':'FORBIDDEN'}
    artifact=out/args.date/stamp/'scan.json'
    save(artifact,{**summary,'brands':rows,'candidate_deltas':changes})
    save(out/'latest.json',{**summary,'artifact_path':str(artifact)})
    report=['# 無料・公式サイト直接収集',f"観測日：{args.date}",'Gemini・Google検索API呼び出し：0回。掲載候補は未承認。全件巡回の完了とは扱いません。',
            f"対象 {len(rows)} ブランド／商品カード取得 {len(product_brands)} ブランド／商品 {summary['product_count']} 件",'',
            '|ブランド|状態|商品・リンク候補|エラー数|','|---|---|---:|---:|']
    report.extend(f"|{r['brand_name']}|{r['scan_status']}|{len(r['surface_items'])}|{len(r['errors'])}|" for r in rows)
    report += ['','未取得・未解析は変更なしと判定しません。過去の商品記録は保持します。詳細と取得元は同じフォルダの scan.json を参照。']
    (artifact.parent/'summary.md').write_text('\n'.join(report)+'\n')
    print(json.dumps(summary,ensure_ascii=False))
    return 0 if len(product_brands)>=39 else 1

if __name__=='__main__':raise SystemExit(main())
