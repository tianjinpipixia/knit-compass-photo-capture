(()=>{
  'use strict';
  const STORAGE_KEY='kc_fabric_inspection_records_v1';
  const SCHEMA_VERSION='1.0.0';
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const normalize=value=>String(value||'').toLowerCase().replace(/[,、／/%％・()（）\-]+/g,' ').replace(/\s+/g,' ').trim();
  const nowIso=()=>new Date().toISOString();
  const localDate=()=>{const date=new Date();date.setMinutes(date.getMinutes()-date.getTimezoneOffset());return date.toISOString().slice(0,10)};
  const newId=()=>`FI-${localDate().replaceAll('-','')}-${Date.now().toString(36).toUpperCase()}-${crypto.getRandomValues(new Uint16Array(1))[0].toString(36).toUpperCase()}`;

  function emptyState(){return{format:'KC_FABRIC_INSPECTION_EXPORT',schema_version:SCHEMA_VERSION,records:[]}}
  function loadState(){try{const parsed=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');return parsed&&Array.isArray(parsed.records)?{...emptyState(),...parsed}:emptyState()}catch{return emptyState()}}
  function saveState(state){localStorage.setItem(STORAGE_KEY,JSON.stringify({...state,format:'KC_FABRIC_INSPECTION_EXPORT',schema_version:SCHEMA_VERSION,updated_at:nowIso()}))}
  function validUrl(value){if(!value)return'';const url=new URL(value);if(!['http:','https:'].includes(url.protocol))throw new Error('根拠URLは http または https を使用してください。');return url.href}
  function setMessage(text,error=false){const target=$('formMessage');target.textContent=text;target.classList.toggle('error',error)}
  function resultLabel(value){return({PASS:'合格',NEEDS_REVIEW:'要確認',FAIL:'不合格'})[value]||value}
  function evidenceLabel(value){return({PHYSICAL_INSPECTION:'現物確認',MEASURED:'実測済み',DOCUMENT_CHECKED:'資料確認済み',UNCONFIRMED:'未確認'})[value]||value}

  function render(){
    const state=loadState();
    const query=normalize($('recordSearch').value);
    const records=[...state.records].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
    $('totalCount').textContent=records.length;
    $('pendingCount').textContent=records.filter(row=>row.review_status==='PENDING_HUMAN_REVIEW').length;
    $('passCount').textContent=records.filter(row=>row.inspection_result==='PASS').length;
    $('attentionCount').textContent=records.filter(row=>['NEEDS_REVIEW','FAIL'].includes(row.inspection_result)).length;
    const visible=records.filter(row=>!query||normalize([row.inspection_id,row.item_ref,row.operator,row.fabric_structure,row.gauge,row.composition,row.inspection_result,row.defect_category,row.notes].join(' ')).includes(query));
    $('recordList').innerHTML=visible.length?visible.map(row=>{
      const resultClass=row.inspection_result==='PASS'?'pass':'attention';
      const facts=[row.inspected_on,row.fabric_structure,row.gauge,row.knitting_ends?`${row.knitting_ends}本取り`:'',row.width,row.weight].filter(Boolean).join(' ／ ');
      return`<article class="record"><div><div class="tags"><span class="tag pending">PENDING HUMAN REVIEW</span><span class="tag ${resultClass}">${esc(resultLabel(row.inspection_result))}</span><span class="tag">${esc(evidenceLabel(row.evidence_status))}</span></div><h3>${esc(row.item_ref)}</h3><p>${esc(row.inspection_id)}／${esc(row.operator)}${facts?`\n${esc(facts)}`:''}${row.composition?`\n混率: ${esc(row.composition)}`:''}${row.notes?`\n${esc(row.notes)}`:''}${row.supersedes_id?`\n訂正元: ${esc(row.supersedes_id)}`:''}</p></div><span class="tag">追記記録</span></article>`;
    }).join(''):'<div class="empty">条件に一致する検査記録はありません。</div>';
  }

  function recordFromForm(form){
    const data=new FormData(form);
    return{
      inspection_id:newId(),
      record_type:'FABRIC_INSPECTION',
      review_status:'PENDING_HUMAN_REVIEW',
      publication_status:'HOLD',
      inspected_on:String(data.get('inspectedOn')||''),
      operator:String(data.get('operator')||'').trim(),
      item_ref:String(data.get('itemRef')||'').trim(),
      fabric_structure:String(data.get('fabricStructure')||'').trim(),
      gauge:String(data.get('gauge')||'').trim(),
      knitting_ends:data.get('knittingEnds')?Number(data.get('knittingEnds')):null,
      composition:String(data.get('composition')||'').trim(),
      width:String(data.get('width')||'').trim(),
      weight:String(data.get('weight')||'').trim(),
      defect_category:String(data.get('defectCategory')||''),
      inspection_result:String(data.get('result')||''),
      evidence_status:String(data.get('evidenceStatus')||''),
      source_url:validUrl(String(data.get('sourceUrl')||'').trim()),
      supersedes_id:String(data.get('supersedesId')||'').trim(),
      notes:String(data.get('notes')||'').trim(),
      created_at:nowIso()
    };
  }

  $('inspectionForm').addEventListener('submit',event=>{
    event.preventDefault();
    try{
      const record=recordFromForm(event.currentTarget);
      if(!record.inspected_on||!record.operator||!record.item_ref)throw new Error('検査日、検査者、参照名を入力してください。');
      const state=loadState();state.records.push(record);saveState(state);
      event.currentTarget.reset();$('inspectedOn').value=localDate();setMessage(`${record.inspection_id} をPENDING_HUMAN_REVIEWで追記しました。`);render();
    }catch(error){setMessage(`保存できませんでした。既存記録は変更していません: ${error.message||error}`,true)}
  });
  $('resetForm').addEventListener('click',()=>setTimeout(()=>{$('inspectedOn').value=localDate();setMessage('')},0));
  $('recordSearch').addEventListener('input',render);
  $('exportJson').addEventListener('click',()=>{
    const state=loadState();
    if(!state.records.length){setMessage('書き出す検査記録がありません。',true);return}
    const blob=new Blob([JSON.stringify({...state,exported_at:nowIso()},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`kc_fabric_inspection_${localDate()}.json`;link.rel='noopener';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);setMessage(`${state.records.length}件の監査JSONを書き出しました。`);
  });
  window.addEventListener('storage',event=>{if(event.key===STORAGE_KEY)render()});
  $('inspectedOn').value=localDate();render();
})();
