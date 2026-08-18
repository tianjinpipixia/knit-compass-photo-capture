(function(root,factory){
  'use strict';
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  if(root)root.KCQualityModel=api;
})(typeof globalThis!=='undefined'?globalThis:this,function(){
  'use strict';

  const REVIEW_PENDING_DECISIONS=new Set(['RETURNED','RECHECK_REQUIRED']);
  const IMPROVEMENT_OPEN_STATUSES=new Set(['OPEN','IN_PROGRESS']);

  const arr=value=>Array.isArray(value)?value:[];
  const newest=(a,b)=>String(b?.created_at||'').localeCompare(String(a?.created_at||''));

  function normalizeState(raw){
    const source=raw&&typeof raw==='object'?raw:{};
    return{
      ...source,
      format:source.format||'KC_FABRIC_INSPECTION_EXPORT',
      schema_version:source.schema_version||'1.1.0',
      records:arr(source.records),
      review_events:arr(source.review_events),
      improvement_events:arr(source.improvement_events)
    };
  }

  function latestEventMap(events,key='inspection_id'){
    const map=new Map();
    [...arr(events)].sort(newest).forEach(event=>{
      const id=String(event?.[key]||'').trim();
      if(id&&!map.has(id))map.set(id,event);
    });
    return map;
  }

  function latestReviewMap(state){return latestEventMap(normalizeState(state).review_events)}
  function latestImprovementMap(state){return latestEventMap(normalizeState(state).improvement_events)}

  function reviewDecision(record,reviewMap){
    const id=String(record?.inspection_id||'');
    return reviewMap.get(id)?.decision||'PENDING_HUMAN_REVIEW';
  }

  function isReviewPending(record,reviewMap){
    const decision=reviewDecision(record,reviewMap);
    return decision==='PENDING_HUMAN_REVIEW'||REVIEW_PENDING_DECISIONS.has(decision);
  }

  function isAppearanceRecord(record){
    const scope=String(record?.inspection_scope||'').toUpperCase();
    if(scope==='APPEARANCE'||scope==='BOTH')return true;
    if(scope)return false;
    const defect=String(record?.defect_category||'');
    return Boolean(defect&&defect!=='NONE_OBSERVED');
  }

  function photoEvidenceCount(record){
    const refs=arr(record?.photo_refs).filter(Boolean);
    return refs.length+(String(record?.photo_capture_id||'').trim()?1:0);
  }

  function computeSummary(input){
    const state=normalizeState(input);
    const reviewMap=latestReviewMap(state);
    const improvementMap=latestImprovementMap(state);
    const records=state.records;
    const total=records.length;
    const fail=records.filter(row=>row.inspection_result==='FAIL').length;
    const pass=records.filter(row=>row.inspection_result==='PASS').length;
    const needsReview=records.filter(row=>row.inspection_result==='NEEDS_REVIEW').length;
    const pending=records.filter(row=>isReviewPending(row,reviewMap)).length;
    const approved=records.filter(row=>reviewDecision(row,reviewMap)==='APPROVED').length;
    const appearance=records.filter(isAppearanceRecord).length;
    const corrections=records.filter(row=>Boolean(String(row.supersedes_id||'').trim())).length;
    const photoEvidence=records.filter(row=>photoEvidenceCount(row)>0).length;
    const improvementCases=new Set(state.improvement_events.map(row=>String(row.inspection_id||'')).filter(Boolean)).size;
    let openImprovements=0;
    let closedImprovements=0;
    improvementMap.forEach(event=>{
      if(IMPROVEMENT_OPEN_STATUSES.has(event.status))openImprovements+=1;
      if(event.status==='VERIFIED'||event.status==='CLOSED')closedImprovements+=1;
    });
    return{
      total,fail,pass,needsReview,pending,approved,appearance,corrections,photoEvidence,
      improvementCases,openImprovements,closedImprovements,
      failRate:total?Math.round((fail/total)*100):0,
      reviewMap,improvementMap
    };
  }

  function matchesFilter(record,filter,input){
    const state=normalizeState(input);
    const summary=computeSummary(state);
    const value=String(filter||'all').toLowerCase();
    if(value==='all'||!value)return true;
    if(value==='pending')return isReviewPending(record,summary.reviewMap);
    if(value==='needs-review')return record.inspection_result==='NEEDS_REVIEW';
    if(value==='fail')return record.inspection_result==='FAIL';
    if(value==='appearance')return isAppearanceRecord(record);
    if(value==='photo')return photoEvidenceCount(record)>0;
    if(value==='improvement')return summary.improvementMap.has(String(record.inspection_id||''));
    return true;
  }

  return{
    normalizeState,
    latestReviewMap,
    latestImprovementMap,
    reviewDecision,
    isReviewPending,
    isAppearanceRecord,
    photoEvidenceCount,
    computeSummary,
    matchesFilter
  };
});
