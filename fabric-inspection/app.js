(()=>{
  'use strict';

  const STORAGE_KEY='kc_fabric_inspection_records_v1';
  const SCHEMA_VERSION='1.1.0';
  const Model=window.KCQualityModel;
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const normalize=value=>String(value||'').toLowerCase().replace(/[,、／/%％・()（）\-]+/g,' ').replace(/\s+/g,' ').trim();
  const nowIso=()=>new Date().toISOString();
  const localDate=()=>{const date=new Date();date.setMinutes(date.getMinutes()-date.getTimezoneOffset());return date.toISOString().slice(0,10)};
  const newId=prefix=>`${prefix}-${localDate().replaceAll('-','')}-${Date.now().toString(36).toUpperCase()}-${crypto.getRandomValues(new Uint16Array(1))[0].toString(36).toUpperCase()}`;

  function emptyState(){return Model.normalizeState({format:'KC_FABRIC_INSPECTION_EXPORT',schema_version:SCHEMA_VERSION,records:[],review_events:[],improvement_events:[]})}
  function loadState(){
    try{return Model.normalizeState(JSON.parse(localStorage.getItem(STORAGE_KEY)||'null'))}
    catch{return emptyState()}
  }
  function saveState(state){
    const normalized=Model.normalizeState(state);
    localStorage.setItem(STORAGE_KEY,JSON.stringify({...normalized,format:'KC_FABRIC_INSPECTION_EXPORT',schema_version:SCHEMA_VERSION,updated_at:nowIso()}));
  }
  function validUrl(value){if(!value)return'';const url=new URL(value);if(!['http:','https:'].includes(url.protocol))throw new Error('根拠URLは http または https を使用してください。');return url.href}
  function setMessage(targetId,text,error=false){const target=$(targetId);target.textContent=text;target.classList.toggle('error',error)}
  function resultLabel(value){return({PASS:'合格',NEEDS_REVIEW:'要確認',FAIL:'不合格'})[value]||value}
  function evidenceLabel(value){return({PHYSICAL_INSPECTION:'現物確認',MEASURED:'実測済み',DOCUMENT_CHECKED:'資料確認済み',UNCONFIRMED:'未確認'})[value]||value}
  function reviewLabel(value){return({APPROVED:'承認済み',RETURNED:'差戻し',RECHECK_REQUIRED:'再確認',PENDING_HUMAN_REVIEW:'Review待ち'})[value]||value}
  function improvementLabel(value){return({OPEN:'未着手',IN_PROGRESS:'対応中',VERIFIED:'効果確認済み',CLOSED:'完了'})[value]||value}
  function splitRefs(value){return String(value||'').split(/[\n,]+/).map(v=>v.trim()).filter(Boolean).slice(0,20)}

  let activeFilter=new URLSearchParams(location.search).get('filter')||'all';

  function setOptions(selectId,records,filterFn=()=>true){
    const select=$(selectId);
    const current=select.value;
    const rows=records.filter(filterFn);
    select.innerHTML='<option value="">対象記録を選択</option>'+rows.map(row=>`<option value="${esc(row.inspection_id)}">${esc(row.inspection_id)}｜${esc(row.item_ref||'参照名未登録')}</option>`).join('');
    if(rows.some(row=>row.inspection_id===current))select.value=current;
  }

  function recordSearchText(row,summary){
    const review=Model.reviewDecision(row,summary.reviewMap);
    const improvement=summary.improvementMap.get(String(row.inspection_id||''));
    return normalize([
      row.inspection_id,row.item_ref,row.operator,row.fabric_structure,row.gauge,row.composition,row.inspection_result,
      row.defect_category,row.notes,row.test_method,row.standard_value,row.measured_value,row.measurement_unit,
      row.photo_capture_id,...(Array.isArray(row.photo_refs)?row.photo_refs:[]),review,improvement?.status,improvement?.cause,improvement?.action
    ].join(' '));
  }

  function render(){
    const state=loadState();
    const summary=Model.computeSummary(state);
    const query=normalize($('recordSearch').value);
    const records=[...state.records].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));

    $('totalCount').textContent=summary.total;
    $('pendingCount').textContent=summary.pending;
    $('passCount').textContent=summary.pass;
    $('attentionCount').textContent=summary.needsReview+summary.fail;
    $('openImprovementCount').textContent=summary.openImprovements;

    setOptions('reviewInspectionId',records,row=>Model.isReviewPending(row,summary.reviewMap)||row.inspection_result!=='PASS');
    setOptions('improvementInspectionId',records);

    const visible=records.filter(row=>Model.matchesFilter(row,activeFilter,state)).filter(row=>!query||recordSearchText(row,summary).includes(query));
    $('recordList').innerHTML=visible.length?visible.map(row=>{
      const resultClass=row.inspection_result==='PASS'?'pass':'attention';
      const review=Model.reviewDecision(row,summary.reviewMap);
      const improvement=summary.improvementMap.get(String(row.inspection_id||''));
      const facts=[
        row.inspected_on,row.inspection_scope==='APPEARANCE'?'外観検品':row.inspection_scope==='BOTH'?'試験＋外観':'生地試験',
        row.fabric_structure,row.gauge,row.knitting_ends?`${row.knitting_ends}本取り`:'',row.width,row.weight
      ].filter(Boolean).join(' ／ ');
      const structured=[row.test_method,row.standard_value?`基準:${row.standard_value}`:'',row.measured_value?`実測:${row.measured_value}${row.measurement_unit||''}`:''].filter(Boolean).join(' ／ ');
      const photos=Model.photoEvidenceCount(row);
      return`<article class="record"><div><div class="tags"><span class="tag ${review==='APPROVED'?'pass':'pending'}">${esc(reviewLabel(review))}</span><span class="tag ${resultClass}">${esc(resultLabel(row.inspection_result))}</span><span class="tag">${esc(evidenceLabel(row.evidence_status))}</span>${improvement?`<span class="tag">${esc(improvementLabel(improvement.status))}</span>`:''}${photos?`<span class="tag">写真根拠 ${photos}</span>`:''}</div><h3>${esc(row.item_ref)}</h3><p>${esc(row.inspection_id)}／${esc(row.operator)}${facts?`\n${esc(facts)}`:''}${structured?`\n${esc(structured)}`:''}${row.composition?`\n混率: ${esc(row.composition)}`:''}${row.photo_capture_id?`\nPhoto Capture: ${esc(row.photo_capture_id)}`:''}${row.notes?`\n${esc(row.notes)}`:''}${row.supersedes_id?`\n訂正元: ${esc(row.supersedes_id)}`:''}</p></div><span class="tag">追記記録</span></article>`;
    }).join(''):'<div class="empty">条件に一致する検査記録はありません。</div>';

    $('recordFilter').value=activeFilter;
    const label={all:'すべて',pending:'Human Review待ち','needs-review':'要確認',fail:'FAIL',appearance:'外観検品',improvement:'改善履歴',photo:'写真根拠あり'}[activeFilter]||'すべて';
    $('filterLabel').textContent=label;
  }

  function recordFromForm(form){
    const data=new FormData(form);
    return{
      inspection_id:newId('FI'),
      record_type:'FABRIC_INSPECTION',
      review_status:'PENDING_HUMAN_REVIEW',
      publication_status:'HOLD',
      inspection_scope:String(data.get('inspectionScope')||'FABRIC_TEST'),
      inspected_on:String(data.get('inspectedOn')||''),
      operator:String(data.get('operator')||'').trim(),
      item_ref:String(data.get('itemRef')||'').trim(),
      fabric_structure:String(data.get('fabricStructure')||'').trim(),
      gauge:String(data.get('gauge')||'').trim(),
      knitting_ends:data.get('knittingEnds')?Number(data.get('knittingEnds')):null,
      composition:String(data.get('composition')||'').trim(),
      width:String(data.get('width')||'').trim(),
      weight:String(data.get('weight')||'').trim(),
      test_method:String(data.get('testMethod')||'').trim(),
      standard_value:String(data.get('standardValue')||'').trim(),
      measured_value:String(data.get('measuredValue')||'').trim(),
      measurement_unit:String(data.get('measurementUnit')||'').trim(),
      defect_category:String(data.get('defectCategory')||''),
      inspection_result:String(data.get('result')||''),
      evidence_status:String(data.get('evidenceStatus')||''),
      photo_capture_id:String(data.get('photoCaptureId')||'').trim(),
      photo_refs:splitRefs(data.get('qualityPhotoRefs')),
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
      const state=loadState();
      state.records.push(record);
      saveState(state);
      event.currentTarget.reset();
      $('inspectedOn').value=localDate();
      applyModeFromUrl();
      setMessage('formMessage',`${record.inspection_id} をPENDING_HUMAN_REVIEWで追記しました。`);
      render();
    }catch(error){setMessage('formMessage',`保存できませんでした。既存記録は変更していません: ${error.message||error}`,true)}
  });

  $('reviewForm').addEventListener('submit',event=>{
    event.preventDefault();
    try{
      const data=new FormData(event.currentTarget);
      const inspectionId=String(data.get('reviewInspectionId')||'').trim();
      const reviewer=String(data.get('reviewer')||'').trim();
      const decision=String(data.get('reviewDecision')||'').trim();
      if(!inspectionId||!reviewer||!decision)throw new Error('対象記録、確認者、判定を入力してください。');
      const state=loadState();
      if(!state.records.some(row=>row.inspection_id===inspectionId))throw new Error('対象の検査記録が見つかりません。');
      const eventRecord={review_id:newId('FR'),record_type:'FABRIC_REVIEW',inspection_id:inspectionId,decision,reviewer,review_note:String(data.get('reviewNote')||'').trim(),created_at:nowIso()};
      state.review_events.push(eventRecord);
      saveState(state);
      event.currentTarget.reset();
      setMessage('reviewMessage',`${eventRecord.review_id} を追記しました。元の検査記録は変更していません。`);
      render();
    }catch(error){setMessage('reviewMessage',`Reviewを保存できませんでした: ${error.message||error}`,true)}
  });

  $('improvementForm').addEventListener('submit',event=>{
    event.preventDefault();
    try{
      const data=new FormData(event.currentTarget);
      const inspectionId=String(data.get('improvementInspectionId')||'').trim();
      const cause=String(data.get('cause')||'').trim();
      const action=String(data.get('action')||'').trim();
      if(!inspectionId||!cause||!action)throw new Error('対象記録、原因、改善策を入力してください。');
      const state=loadState();
      if(!state.records.some(row=>row.inspection_id===inspectionId))throw new Error('対象の検査記録が見つかりません。');
      const eventRecord={
        improvement_id:newId('FC'),record_type:'FABRIC_IMPROVEMENT',inspection_id:inspectionId,
        cause,action,owner:String(data.get('improvementOwner')||'').trim(),due_date:String(data.get('dueDate')||''),
        verification:String(data.get('verification')||'').trim(),status:String(data.get('improvementStatus')||'OPEN'),created_at:nowIso()
      };
      state.improvement_events.push(eventRecord);
      saveState(state);
      event.currentTarget.reset();
      setMessage('improvementMessage',`${eventRecord.improvement_id} を改善履歴として追記しました。`);
      render();
    }catch(error){setMessage('improvementMessage',`改善履歴を保存できませんでした: ${error.message||error}`,true)}
  });

  function applyModeFromUrl(){
    const mode=new URLSearchParams(location.search).get('mode');
    if(mode==='appearance')$('inspectionScope').value='APPEARANCE';
    else if(mode==='test')$('inspectionScope').value='FABRIC_TEST';
  }

  $('resetForm').addEventListener('click',()=>setTimeout(()=>{$('inspectedOn').value=localDate();applyModeFromUrl();setMessage('formMessage','')},0));
  $('recordSearch').addEventListener('input',render);
  $('recordFilter').addEventListener('change',event=>{activeFilter=event.target.value;render()});
  $('exportJson').addEventListener('click',()=>{
    const state=loadState();
    if(!state.records.length){setMessage('formMessage','書き出す検査記録がありません。',true);return}
    const blob=new Blob([JSON.stringify({...state,exported_at:nowIso()},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');
    link.href=url;link.download=`kc_fabric_quality_${localDate()}.json`;link.rel='noopener';
    document.body.appendChild(link);link.click();link.remove();
    setTimeout(()=>URL.revokeObjectURL(url),30000);
    setMessage('formMessage',`${state.records.length}件の検査記録とReview・改善イベントを書き出しました。`);
  });
  window.addEventListener('storage',event=>{if(event.key===STORAGE_KEY)render()});

  $('inspectedOn').value=localDate();
  applyModeFromUrl();
  render();
})();
