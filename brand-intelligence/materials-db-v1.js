(()=>{
  'use strict';
  const V04_KEY='kc_independent_practical_v0_4';
  const VERSION='1.0.0';
  const TYPES=new Set(['fiber_generic','branded_fiber','polymer','filament','functional_additive','functional_technology','dye_finish','processing_technology','other']);
  const FORMS=new Set(['staple','filament','chip_resin','additive','finish','technology','unknown']);
  const STATUSES=new Set(['unconfirmed','candidate','supplier_claim','document_confirmed','test_confirmed','confirmed','conflicting']);
  const RELATIONSHIPS=new Set(['bulk','core','sheath','cover','plating','blend_component','finish','additive','technology','unknown']);
  const now=()=>new Date().toISOString();
  const uuid=()=>crypto.randomUUID?.()||`${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const uniq=value=>[...new Set((Array.isArray(value)?value:[]).map(v=>String(v||'').trim()).filter(Boolean))];
  const text=value=>String(value??'').trim();
  const arr=value=>Array.isArray(value)?value:[];
  const object=value=>value&&typeof value==='object'&&!Array.isArray(value)?value:{};

  function loadState(){
    try{
      const parsed=JSON.parse(localStorage.getItem(V04_KEY)||'{}');
      return parsed&&typeof parsed==='object'?parsed:{};
    }catch{return{}}
  }
  function saveState(state){
    state.updated_at=now();
    localStorage.setItem(V04_KEY,JSON.stringify(state));
    return state;
  }
  function normalizeEvidence(value){
    return arr(value).map(row=>({
      evidenceId:text(row?.evidenceId||row?.id),
      sourceType:text(row?.sourceType),
      sourceUrl:text(row?.sourceUrl),
      observedAt:text(row?.observedAt),
      status:STATUSES.has(row?.status)?row.status:'unconfirmed',
      fields:uniq(row?.fields),
      note:text(row?.note)
    })).filter(row=>row.evidenceId||row.sourceUrl||row.note);
  }
  function normalizeMaterial(row={}){
    const legacyName=text(row.name||row.materialName||row.tradeName)||'素材名未確認';
    const status=STATUSES.has(row.verificationStatus)?row.verificationStatus:(row.verificationStatus==='confirmed'?'confirmed':'unconfirmed');
    return{
      ...row,
      id:text(row.id||row.commonId)||`MT-${uuid()}`,
      commonId:text(row.commonId||row.id)||'',
      name:legacyName,
      tradeName:text(row.tradeName),
      aliases:uniq(row.aliases),
      materialType:TYPES.has(row.materialType)?row.materialType:'other',
      fiberPolymer:text(row.fiberPolymer),
      form:FORMS.has(row.form)?row.form:'unknown',
      manufacturerOrganizationId:text(row.manufacturerOrganizationId),
      supplierOrganizationIds:uniq(row.supplierOrganizationIds),
      composition:text(row.composition),
      functionalProperties:arr(row.functionalProperties),
      sustainableAttributes:arr(row.sustainableAttributes),
      evidence:normalizeEvidence(row.evidence),
      linkedYarnIds:uniq(row.linkedYarnIds),
      linkedProductIds:uniq(row.linkedProductIds),
      relationships:arr(row.relationships).map(rel=>({
        targetType:['yarn','product'].includes(rel?.targetType)?rel.targetType:'yarn',
        targetId:text(rel?.targetId),
        role:RELATIONSHIPS.has(rel?.role)?rel.role:'unknown',
        note:text(rel?.note)
      })).filter(rel=>rel.targetId),
      commercial:{
        currency:text(object(row.commercial).currency),
        price:text(object(row.commercial).price),
        unit:text(object(row.commercial).unit),
        moq:text(object(row.commercial).moq),
        leadTime:text(object(row.commercial).leadTime),
        terms:text(object(row.commercial).terms),
        priceObservedAt:text(object(row.commercial).priceObservedAt)
      },
      verificationStatus:status,
      notes:text(row.notes),
      created_at:text(row.created_at)||now(),
      updated_at:text(row.updated_at)||now()
    };
  }
  function ensureState(state){
    if(!Array.isArray(state.materials))state.materials=[];
    state.materials=state.materials.map(normalizeMaterial).map(row=>({...row,commonId:row.commonId||row.id}));
    return state;
  }
  function migrate(){
    const state=ensureState(loadState());
    saveState(state);
    return state.materials;
  }
  function upsert(input){
    const state=ensureState(loadState());
    const normalized=normalizeMaterial(input);
    normalized.commonId=normalized.commonId||normalized.id;
    const index=state.materials.findIndex(row=>row.id===normalized.id||row.commonId===normalized.commonId);
    if(index>=0){
      normalized.created_at=state.materials[index].created_at||normalized.created_at;
      normalized.updated_at=now();
      state.materials[index]=normalized;
    }else{
      normalized.created_at=now();normalized.updated_at=normalized.created_at;
      state.materials.unshift(normalized);
    }
    saveState(state);
    return normalized;
  }
  function link(materialId,{targetType,targetId,role='unknown',note=''}){
    if(!['yarn','product'].includes(targetType))throw new Error('targetType must be yarn or product');
    if(!RELATIONSHIPS.has(role))throw new Error('unknown relationship role');
    const state=ensureState(loadState());
    const row=state.materials.find(item=>item.id===materialId||item.commonId===materialId);
    if(!row)throw new Error('material not found');
    const list=targetType==='yarn'?'linkedYarnIds':'linkedProductIds';
    row[list]=uniq([...(row[list]||[]),targetId]);
    const key=`${targetType}:${targetId}:${role}`;
    const relationships=arr(row.relationships).filter(rel=>`${rel.targetType}:${rel.targetId}:${rel.role}`!==key);
    relationships.push({targetType,targetId:text(targetId),role,note:text(note)});
    row.relationships=relationships;row.updated_at=now();
    saveState(state);
    return row;
  }
  function search(query=''){
    const q=text(query).toLowerCase();
    return ensureState(loadState()).materials.filter(row=>{
      if(!q)return true;
      return [
        row.name,row.tradeName,row.fiberPolymer,row.materialType,row.form,row.composition,
        ...(row.aliases||[]),...(row.supplierOrganizationIds||[]),row.notes
      ].join(' ').toLowerCase().includes(q);
    });
  }
  window.KnitCompassMaterialsDB=Object.freeze({
    version:VERSION,load:()=>ensureState(loadState()).materials,migrate,normalizeMaterial,upsert,link,search
  });
  migrate();
})();
