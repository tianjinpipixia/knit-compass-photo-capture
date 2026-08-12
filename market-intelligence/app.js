(()=>{
  'use strict';
  const STORAGE_KEY='kc_market_intelligence_observations_v1';
  const SCHEMA_VERSION='1.0.0';
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const normalize=value=>String(value||'').toLowerCase().replace(/[,、／/%％・()（）\-]+/g,' ').replace(/\s+/g,' ').trim();
  const nowIso=()=>new Date().toISOString();
  const localDate=()=>{const date=new Date();date.setMinutes(date.getMinutes()-date.getTimezoneOffset());return date.toISOString().slice(0,10)};
  const newId=()=>`MI-${localDate().replaceAll('-','')}-${Date.now().toString(36).toUpperCase()}-${crypto.getRandomValues(new Uint16Array(1))[0].toString(36).toUpperCase()}`;
  const materialLabels={WOOL:'羊毛',CASHMERE:'カシミヤ',COTTON:'綿',LINEN:'麻',VISCOSE:'レーヨン／ビスコース',POLYESTER:'ポリエステル',NYLON:'ナイロン',ACRYLIC:'アクリル',OTHER:'その他'};
  const evidenceLabels={SOURCE_CHECKED:'原資料確認済み',SUPPLIER_CONFIRMED:'Supplier確認済み',SECONDARY_SOURCE:'二次資料',UNCONFIRMED:'未確認'};
  const directionLabels={UNKNOWN:'不明・未比較',UP:'上昇',FLAT:'横ばい',DOWN:'下落',VOLATILE:'変動大'};

  function emptyState(){return{format:'KC_MARKET_INTELLIGENCE_EXPORT',schema_version:SCHEMA_VERSION,observations:[]}}
  function loadState(){try{const parsed=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');return parsed&&Array.isArray(parsed.observations)?{...emptyState(),...parsed}:emptyState()}catch{return emptyState()}}
  function saveState(state){localStorage.setItem(STORAGE_KEY,JSON.stringify({...state,format:'KC_MARKET_INTELLIGENCE_EXPORT',schema_version:SCHEMA_VERSION,updated_at:nowIso()}))}
  function validUrl(value){if(!value)return'';const url=new URL(value);if(!['http:','https:'].includes(url.protocol))throw new Error('根拠URLは http または https を使用してください。');return url.href}
  function setMessage(text,error=false){const target=$('formMessage');target.textContent=text;target.classList.toggle('error',error)}

  function render(){
    const state=loadState();
    const query=normalize($('recordSearch').value);
    const rows=[...state.observations].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
    $('totalCount').textContent=rows.length;
    $('pendingCount').textContent=rows.filter(row=>row.review_status==='PENDING_HUMAN_REVIEW').length;
    $('verifiedCount').textContent=rows.filter(row=>['SOURCE_CHECKED','SUPPLIER_CONFIRMED'].includes(row.evidence_status)).length;
    $('materialCount').textContent=new Set(rows.map(row=>row.material).filter(Boolean)).size;
    const visible=rows.filter(row=>!query||normalize([row.observation_id,materialLabels[row.material],row.market,row.indicator,row.source_name,row.quote,row.currency,row.unit,row.direction,row.notes].join(' ')).includes(query));
    $('recordList').innerHTML=visible.length?visible.map(row=>{
      const directionClass=row.direction==='UP'||row.direction==='VOLATILE'?'up':row.direction==='DOWN'?'down':'flat';
      const quote=[row.quote,row.currency,row.unit?`/ ${row.unit}`:''].filter(Boolean).join(' ');
      return`<article class="record"><div><div class="tags"><span class="tag pending">PENDING HUMAN REVIEW</span><span class="tag ${directionClass}">${esc(directionLabels[row.direction]||row.direction)}</span><span class="tag">${esc(evidenceLabels[row.evidence_status]||row.evidence_status)}</span></div><h3>${esc(materialLabels[row.material]||row.material)}｜${esc(row.market)}</h3><p>${esc(row.observation_id)}／${esc(row.observed_on)}${row.indicator?`\n${esc(row.indicator)}`:''}\n情報源: ${esc(row.source_name)}${row.notes?`\n${esc(row.notes)}`:''}</p></div><div class="quote"><strong>${esc(quote||'定性観測')}</strong><span>自動換算なし</span></div></article>`;
    }).join(''):'<div class="empty">条件に一致する相場観測はありません。</div>';
  }

  function observationFromForm(form){
    const data=new FormData(form);
    return{
      observation_id:newId(),
      record_type:'RAW_MATERIAL_MARKET_OBSERVATION',
      review_status:'PENDING_HUMAN_REVIEW',
      publication_status:'HOLD',
      observed_on:String(data.get('observedOn')||''),
      material:String(data.get('material')||''),
      market:String(data.get('market')||'').trim(),
      indicator:String(data.get('indicator')||'').trim(),
      quote:String(data.get('quote')||'').trim(),
      currency:String(data.get('currency')||'').trim().toUpperCase(),
      unit:String(data.get('unit')||'').trim(),
      direction:String(data.get('direction')||'UNKNOWN'),
      evidence_status:String(data.get('evidenceStatus')||''),
      source_name:String(data.get('sourceName')||'').trim(),
      source_url:validUrl(String(data.get('sourceUrl')||'').trim()),
      notes:String(data.get('notes')||'').trim(),
      created_at:nowIso()
    };
  }

  $('marketForm').addEventListener('submit',event=>{
    event.preventDefault();
    try{
      const row=observationFromForm(event.currentTarget);
      if(!row.observed_on||!row.material||!row.market||!row.source_name)throw new Error('観測日、原料、市場・地域、情報源名を入力してください。');
      const state=loadState();state.observations.push(row);saveState(state);
      event.currentTarget.reset();$('observedOn').value=localDate();setMessage(`${row.observation_id} をPENDING_HUMAN_REVIEWで追記しました。`);render();
    }catch(error){setMessage(`保存できませんでした。既存記録は変更していません: ${error.message||error}`,true)}
  });
  $('resetForm').addEventListener('click',()=>setTimeout(()=>{$('observedOn').value=localDate();setMessage('')},0));
  $('recordSearch').addEventListener('input',render);
  $('exportJson').addEventListener('click',()=>{
    const state=loadState();
    if(!state.observations.length){setMessage('書き出す相場観測がありません。',true);return}
    const blob=new Blob([JSON.stringify({...state,exported_at:nowIso()},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`kc_market_intelligence_${localDate()}.json`;link.rel='noopener';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);setMessage(`${state.observations.length}件の監査JSONを書き出しました。`);
  });
  window.addEventListener('storage',event=>{if(event.key===STORAGE_KEY)render()});
  $('observedOn').value=localDate();render();
})();
