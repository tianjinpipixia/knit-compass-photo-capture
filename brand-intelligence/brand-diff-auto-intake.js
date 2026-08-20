(()=>{
  'use strict';

  const HANDOFF_KEY='kc_v04_handoff_queue_v1';
  const QUEUE_LIMIT=500;
  const SOURCE_SYSTEM='KC-BRAND64-DIFF';
  const DATA_CONTRACT_VERSION='1.2.0';
  const LOOKBACK_DAYS=7;
  const NBB_NAME='NATURAL BEAUTY BASIC';
  const NBB_ID='BR-00051';
  const NBB_CANONICAL_URL='https://mix.tokyo/pages/naturalbeautybasic';
  const SIGNAL_RE=/(^|[_/\s-])(NEW|PREORDER|RESERVATION|RESTOCK|NEW_COLOR|SALE|SOLD_OUT|ON_SALE|LAUNCH|RELEASED)([_/\s-]|$)/i;
  const SKIP_STATE_RE=/(FRESHNESS_LIMITED|LIGHT_SCAN_OBSERVED|NO_CHANGE|UNCHANGED)/i;

  const now=()=>new Date().toISOString();
  const jstDate=(date=new Date())=>new Date(date.getTime()+9*60*60*1000).toISOString().slice(0,10);
  const dateMinus=(isoDate,days)=>{
    const base=new Date(`${isoDate}T00:00:00Z`);
    base.setUTCDate(base.getUTCDate()-days);
    return base.toISOString().slice(0,10);
  };
  const normalize=value=>String(value??'').normalize('NFKC').replace(/\s+/g,' ').trim();
  const safeArray=value=>Array.isArray(value)?value:[];
  const isCaptured=value=>normalize(value)&&!/^NOT_CAPTURED(?:_|$)/i.test(normalize(value));
  const stableStringify=value=>{
    if(Array.isArray(value))return`[${value.map(stableStringify).join(',')}]`;
    if(value&&typeof value==='object')return`{${Object.keys(value).sort().map(key=>`${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
    return JSON.stringify(value);
  };
  const hash=value=>{
    let h=2166136261;
    const text=String(value);
    for(let i=0;i<text.length;i++){
      h^=text.charCodeAt(i);
      h=Math.imul(h,16777619);
    }
    return(h>>>0).toString(16).padStart(8,'0');
  };
  const parseJsonl=text=>String(text||'').split(/\r?\n/).map(line=>line.trim()).filter(Boolean).flatMap(line=>{try{return[JSON.parse(line)]}catch(error){console.warn('[KC] invalid Brand64 JSONL row skipped',error,line);return[]}});

  function queueKey(item){return item?.dedupe_key||item?.handoff_id||''}
  function compactQueue(queue){
    const ordered=[...queue].sort((a,b)=>String(b.sent_at||'').localeCompare(String(a.sent_at||'')));
    const deduped=[];const seen=new Set();
    for(const item of ordered){const key=queueKey(item);if(key&&seen.has(key))continue;if(key)seen.add(key);deduped.push(item)}
    const pending=deduped.filter(item=>item.review_status==='PENDING');
    const reviewed=deduped.filter(item=>item.review_status!=='PENDING');
    const reviewedSlots=Math.max(0,QUEUE_LIMIT-pending.length);
    return[...pending,...reviewed.slice(0,reviewedSlots)].sort((a,b)=>String(b.sent_at||'').localeCompare(String(a.sent_at||'')));
  }
  function loadQueue(){try{const parsed=JSON.parse(localStorage.getItem(HANDOFF_KEY)||'[]');return Array.isArray(parsed)?parsed:[]}catch{return[]}}
  function saveQueue(queue){localStorage.setItem(HANDOFF_KEY,JSON.stringify(compactQueue(queue)))}

  function productIdentity(row){
    const brand=normalize(row.b||row.brand||'UNKNOWN');
    const code=normalize(row.code);
    if(isCaptured(code))return`${brand}|CODE:${code}`;
    const dedupe=normalize(row.dedupe);
    if(dedupe)return`${brand}|DISCOVERY:${dedupe}`;
    return`${brand}|TITLE:${normalize(row.name)}`;
  }
  function trackedProductFields(row){
    return{
      state:normalize(row.state),
      regular_price_yen:row.regular_price_yen??null,
      sale_price_yen:row.sale_price_yen??null,
      composition_raw:normalize(row.composition_raw||row.composition||''),
      composition_status:normalize(row.composition_status),
      function:safeArray(row.function).map(normalize).filter(Boolean).sort(),
      color:Array.isArray(row.color)?row.color.map(normalize).filter(Boolean).sort():normalize(row.color),
      source:normalize(row.source),
      note:normalize(row.note)
    };
  }
  function hasMeaningfulSignal(row){
    const state=normalize(row.state);
    if(!state||SKIP_STATE_RE.test(state))return false;
    return SIGNAL_RE.test(state)||/NEW|予約|PRE\s*ORDER|再入荷|再販|値下|SALE|SOLD\s*OUT|発売/i.test(state);
  }
  function productFingerprint(row){return hash(stableStringify({identity:productIdentity(row),fields:trackedProductFields(row)}))}
  function productHandoff(row){
    const identity=productIdentity(row);
    const fingerprint=productFingerprint(row);
    const captureId=`BRDIFF-${normalize(row.d||jstDate()).replaceAll('-','')}-${hash(identity)}`;
    const code=isCaptured(row.code)?normalize(row.code):'';
    const source=normalize(row.source);
    const fields=trackedProductFields(row);
    const notes=[
      `Brand64差分スナップショット ${normalize(row.d||'日付未確認')}`,
      `販売状態: ${fields.state||'未確認'}`,
      fields.regular_price_yen!==null?`通常価格: ¥${fields.regular_price_yen}`:'',
      fields.sale_price_yen!==null?`セール価格: ¥${fields.sale_price_yen}`:'',
      source?`取得元: ${source}`:'',
      fields.note,
      '商品ページ直URL・品番・混率が未取得の項目はHuman Reviewで確定する。カテゴリ/ブランドURLだけでは公式商品ページ確定と扱わない。'
    ].filter(Boolean).join(' / ');
    return{
      format:'KC_V04_INBOX_ITEM',
      schema_version:'1.1',
      handoff_id:`HF-BRANDDIFF-${fingerprint.toUpperCase()}`,
      capture_id:captureId,
      event_version:1,
      sent_at:now(),
      source_system:SOURCE_SYSTEM,
      dedupe_key:`BRANDDIFF|${identity}|${fingerprint}`,
      review_status:'PENDING',
      automatic_master_promotion:'FORBIDDEN',
      payload:{
        dataContractVersion:DATA_CONTRACT_VERSION,
        captureId,
        priority:'HIGH',
        targetType:'product',
        targetId:'',
        commonIds:{},
        brandName:normalize(row.b),
        productName:normalize(row.name),
        productCode:code,
        productUrl:'',
        sourceUrl:source,
        releaseStatus:fields.state||'UNKNOWN',
        regularPrice:fields.regular_price_yen,
        salePrice:fields.sale_price_yen,
        compositionRaw:fields.composition_raw,
        compositionStatus:isCaptured(fields.composition_status)?fields.composition_status:'unconfirmed',
        functionalProperties:fields.function.map(name=>({name,source:'brand64_snapshot'})),
        sustainableAttributes:[],
        verificationStatus:'candidate',
        notes,
        fieldEvidence:{
          brandDiffSnapshot:{status:'captured_for_human_review',observedDate:normalize(row.d),identity,fingerprint,raw:row},
          officialProductPage:{status:'not_confirmed_do_not_promote',sourceUrl:source}
        }
      }
    };
  }

  function nbbResearchHandoff(row){
    const observedDate=normalize(row.d||jstDate());
    const evidence={status:normalize(row.s),fact:normalize(row.f),market:normalize(row.m),nextAction:normalize(row.n),url:normalize(row.u)||NBB_CANONICAL_URL};
    const fingerprint=hash(stableStringify(evidence));
    const captureId=`BRDIFF-${observedDate.replaceAll('-','')}-NBB-RECHECK`;
    return{
      format:'KC_V04_INBOX_ITEM',schema_version:'1.1',handoff_id:`HF-BRANDDIFF-NBB-${fingerprint.toUpperCase()}`,
      capture_id:captureId,event_version:1,sent_at:now(),source_system:SOURCE_SYSTEM,
      dedupe_key:`BRANDDIFF|NBB|RECHECK|${fingerprint}`,review_status:'PENDING',automatic_master_promotion:'FORBIDDEN',
      payload:{
        dataContractVersion:DATA_CONTRACT_VERSION,captureId,priority:'HIGH',targetType:'research',targetId:'TMP-RS-NBB-LIVE-RECHECK',commonIds:{},
        brandName:NBB_NAME,productName:'',productCode:'',productUrl:'',sourceUrl:NBB_CANONICAL_URL,
        verificationStatus:'candidate',compositionRaw:'',compositionStatus:'unconfirmed',functionalProperties:[],sustainableAttributes:[],
        notes:[
          `NBBライブ再確認候補 ${observedDate}`,
          evidence.fact,
          evidence.market,
          evidence.nextAction?`次の確認: ${evidence.nextAction}`:'',
          '現時点では索引鮮度だけで当日新商品とは断定しない。mix.tokyoの直接商品ページで品番・販売状態・混率・色を確認後に商品候補化する。'
        ].filter(Boolean).join(' / '),
        fieldEvidence:{brandDailyObservation:{status:'source_url_migrated_recheck_required',raw:row},canonicalSource:{status:'confirmed_current_brand_entry',url:NBB_CANONICAL_URL}}
      }
    };
  }

  async function fetchText(path){
    const response=await fetch(path,{cache:'no-store'});
    if(!response.ok)throw new Error(`${path}: HTTP ${response.status}`);
    return response.text();
  }
  async function firstExisting(kind,startDate,maxDays=LOOKBACK_DAYS){
    for(let offset=0;offset<=maxDays;offset++){
      const date=dateMinus(startDate,offset);
      const path=`../data/brand-md-monitoring/${date}-${kind}.jsonl`;
      try{return{date,path,rows:parseJsonl(await fetchText(path))}}catch(error){if(!/HTTP 404/.test(String(error)))console.warn('[KC] Brand64 auto-intake fetch skipped',error)}
    }
    return null;
  }

  function addUnique(queue,items){
    const keys=new Set(queue.map(queueKey).filter(Boolean));
    let added=0;
    for(const item of items){const key=queueKey(item);if(!key||keys.has(key))continue;queue.unshift(item);keys.add(key);added++}
    return added;
  }

  async function run(){
    if(typeof localStorage==='undefined'||typeof fetch!=='function')return{added:0,reason:'unsupported'};
    const today=jstDate();
    const current=await firstExisting('product-baseline-snapshots',today,3);
    const items=[];
    if(current){
      for(const row of current.rows){
        if(!normalize(row?.b)||!normalize(row?.name))continue;
        if(hasMeaningfulSignal(row))items.push(productHandoff(row));
      }
    }
    const daily=await firstExisting('brand64-daily',current?.date||today,3);
    const nbb=daily?.rows?.find(row=>normalize(row.id)===NBB_ID||normalize(row.b)===NBB_NAME);
    if(nbb&&(/SOURCE_URL_MIGRATED/i.test(normalize(nbb.s))||normalize(nbb.u)===NBB_CANONICAL_URL)){
      const nbbHasProduct=items.some(item=>normalize(item.payload?.brandName)===NBB_NAME);
      if(!nbbHasProduct)items.push(nbbResearchHandoff(nbb));
    }
    const queue=loadQueue();
    const added=addUnique(queue,items);
    if(added){saveQueue(queue);window.dispatchEvent(new CustomEvent('kc:human-review-queue-updated',{detail:{added,source:SOURCE_SYSTEM,observedDate:current?.date||daily?.date||today}}))}
    return{added,candidates:items.length,observedDate:current?.date||daily?.date||today};
  }

  const api={run,parseJsonl,productIdentity,trackedProductFields,hasMeaningfulSignal,productFingerprint,productHandoff,nbbResearchHandoff,compactQueue};
  if(typeof window!=='undefined'){
    window.KCBrandDiffAutoIntake=api;
    const launch=()=>run().catch(error=>console.warn('[KC] Brand64 Human Review auto-intake unavailable',error));
    if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',launch,{once:true});else launch();
  }
})();
