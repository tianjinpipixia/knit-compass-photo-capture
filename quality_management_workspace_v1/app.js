(()=>{
  'use strict';

  const polish=document.createElement('link');
  polish.rel='stylesheet';
  polish.href='./ui-polish.css?v=1.1.0';
  document.head.appendChild(polish);

  const STORAGE_KEY='kc_fabric_inspection_records_v1';
  const Model=window.KCQualityModel;
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));

  function loadState(){
    try{return Model.normalizeState(JSON.parse(localStorage.getItem(STORAGE_KEY)||'null'))}
    catch{return Model.normalizeState(null)}
  }

  function resultLabel(value){return({PASS:'合格',NEEDS_REVIEW:'要確認',FAIL:'不合格'})[value]||'未判定'}
  function resultClass(value){if(value==='PASS')return'pass';if(value==='FAIL')return'fail';return'attn'}
  function reviewLabel(value){return({APPROVED:'Review済み',RETURNED:'差戻し',RECHECK_REQUIRED:'再確認',PENDING_HUMAN_REVIEW:'Review待ち'})[value]||value}
  function dateLabel(value){
    if(!value)return'日付未登録';
    const date=new Date(value);
    if(Number.isNaN(date.getTime()))return String(value).slice(0,10);
    return new Intl.DateTimeFormat('ja-JP',{year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
  }

  function renderRecent(records,summary){
    const target=$('recentList');
    const recent=records.slice(0,5);
    if(!recent.length){
      target.innerHTML='<div class="recent-empty">検査記録はまだありません。</div>';
      return;
    }
    target.innerHTML=recent.map(row=>{
      const meta=[dateLabel(row.inspected_on||row.created_at),row.inspection_id,row.operator].filter(Boolean).join(' ／ ');
      const review=Model.reviewDecision(row,summary.reviewMap);
      return `<article class="recent-item"><div><h4>${esc(row.item_ref||'参照名未登録')}</h4><p>${esc(meta)} ／ ${esc(reviewLabel(review))}</p></div><span class="result ${resultClass(row.inspection_result)}">${esc(resultLabel(row.inspection_result))}</span></article>`;
    }).join('');
  }

  function render(){
    const state=loadState();
    const records=[...state.records].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
    const summary=Model.computeSummary(state);

    $('testCount').textContent=summary.total;
    $('appearanceCount').textContent=summary.appearance;
    $('reviewQueueCount').textContent=summary.pending;
    $('improvementCount').textContent=summary.improvementCases+summary.corrections;

    $('pendingCount').textContent=summary.pending;
    $('reviewCount').textContent=summary.needsReview;
    $('failCount').textContent=summary.fail;
    $('openImprovementCount').textContent=summary.openImprovements;

    $('totalCount').textContent=summary.total;
    $('passCount').textContent=summary.pass;
    $('failRate').textContent=`${summary.failRate}%`;
    $('approvedCount').textContent=summary.approved;
    $('closedImprovementCount').textContent=summary.closedImprovements;
    $('photoEvidenceCount').textContent=summary.photoEvidence;
    renderRecent(records,summary);
  }

  $('refreshButton').addEventListener('click',render);
  window.addEventListener('storage',event=>{if(event.key===STORAGE_KEY)render()});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')render()});
  render();
})();
