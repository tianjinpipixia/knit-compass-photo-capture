(()=>{
  'use strict';

  const STORAGE_KEY='kc_fabric_inspection_records_v1';
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));

  function emptyState(){return{records:[]}}
  function loadState(){
    try{
      const parsed=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');
      return parsed&&Array.isArray(parsed.records)?parsed:emptyState();
    }catch{
      return emptyState();
    }
  }

  function resultLabel(value){
    return({PASS:'合格',NEEDS_REVIEW:'要確認',FAIL:'不合格'})[value]||'未判定';
  }

  function resultClass(value){
    if(value==='PASS')return'pass';
    if(value==='FAIL')return'fail';
    return'attn';
  }

  function dateLabel(value){
    if(!value)return'日付未登録';
    const date=new Date(value);
    if(Number.isNaN(date.getTime()))return String(value).slice(0,10);
    return new Intl.DateTimeFormat('ja-JP',{year:'numeric',month:'2-digit',day:'2-digit'}).format(date);
  }

  function renderRecent(records){
    const target=$('recentList');
    const recent=records.slice(0,5);
    if(!recent.length){
      target.innerHTML='<div class="recent-empty">検査記録はまだありません。</div>';
      return;
    }
    target.innerHTML=recent.map(row=>{
      const meta=[dateLabel(row.inspected_on||row.created_at),row.inspection_id,row.operator].filter(Boolean).join(' ／ ');
      return `<article class="recent-item"><div><h4>${esc(row.item_ref||'参照名未登録')}</h4><p>${esc(meta)}</p></div><span class="result ${resultClass(row.inspection_result)}">${esc(resultLabel(row.inspection_result))}</span></article>`;
    }).join('');
  }

  function render(){
    const records=[...loadState().records].sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
    const total=records.length;
    const pending=records.filter(row=>row.review_status==='PENDING_HUMAN_REVIEW').length;
    const review=records.filter(row=>row.inspection_result==='NEEDS_REVIEW').length;
    const fail=records.filter(row=>row.inspection_result==='FAIL').length;
    const pass=records.filter(row=>row.inspection_result==='PASS').length;
    const appearance=records.filter(row=>Boolean(row.defect_category)).length;
    const corrections=records.filter(row=>Boolean(String(row.supersedes_id||'').trim())).length;

    $('testCount').textContent=total;
    $('appearanceCount').textContent=appearance;
    $('improvementCount').textContent=corrections;
    $('pendingCount').textContent=pending;
    $('reviewCount').textContent=review;
    $('failCount').textContent=fail;
    $('correctionCount').textContent=corrections;
    $('totalCount').textContent=total;
    $('passCount').textContent=pass;
    $('failRate').textContent=total?`${Math.round((fail/total)*100)}%`:'0%';
    renderRecent(records);
  }

  $('refreshButton').addEventListener('click',render);
  window.addEventListener('storage',event=>{if(event.key===STORAGE_KEY)render()});
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')render()});
  render();
})();
