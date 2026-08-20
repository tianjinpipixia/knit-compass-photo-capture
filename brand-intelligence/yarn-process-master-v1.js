(()=>{
  'use strict';

  const V04_KEY='kc_independent_practical_v0_4';
  const HANDOFF_KEY='kc_v04_handoff_queue_v1';
  const PRE_OPTIONS=[['unconfirmed','未確認'],['carded','カード'],['combed','コーマ'],['semi_combed','セミコーマ'],['other','その他']];
  const SPIN_OPTIONS=[['unconfirmed','未確認'],['ring','リング'],['compact','コンパクト'],['mvs_vortex','MVS・VORTEX'],['air_jet','エアジェット'],['oe_rotor','OE・ローター'],['other','その他（原文保持）']];
  const PRE_LABEL={unconfirmed:'未確認',carded:'カード',combed:'コーマ',semi_combed:'セミコーマ',other:'その他'};
  const SPIN_LABEL={unconfirmed:'未確認',ring:'リング',compact:'コンパクト',mvs_vortex:'MVS・VORTEX',air_jet:'エアジェット',oe_rotor:'OE・ローター',other:'その他'};

  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const normalize=value=>String(value||'').trim().normalize('NFKC');
  function normalizePre(value){
    const original=normalize(value),raw=original.toLowerCase();
    if(['unconfirmed','carded','combed','semi_combed','other'].includes(original))return original;
    if(!raw||raw==='unknown'||raw==='未確認')return'unconfirmed';
    if(/semi.?combed|半精梳|セミコーマ/.test(raw))return'semi_combed';
    if(/combed|精梳|コーマ/.test(raw))return'combed';
    if(/carded|普梳|カード/.test(raw))return'carded';
    return'other';
  }
  function normalizeSpin(value){
    const original=normalize(value),raw=original.toLowerCase();
    if(['unconfirmed','ring','compact','mvs_vortex','air_jet','oe_rotor','other'].includes(original))return original;
    if(!raw||raw==='unknown'||raw==='未確認')return'unconfirmed';
    if(/compact|紧密纺|コンパクト/.test(raw))return'compact';
    if(/mvs|vortex|涡流纺|渦流/.test(raw))return'mvs_vortex';
    if(/air.?jet|喷气纺|エアジェット/.test(raw))return'air_jet';
    if(/open.?end|\boe\b|rotor|气流纺|转杯纺|ローター/.test(raw))return'oe_rotor';
    if(/^ring$|环锭纺|リング/.test(raw))return'ring';
    return'other';
  }
  const optionsHtml=(options,selected)=>options.map(([value,label])=>`<option value="${value}" ${value===selected?'selected':''}>${label}</option>`).join('');
  function readJson(storage,key,fallback){try{return JSON.parse(storage.getItem(key)||JSON.stringify(fallback))}catch{return fallback}}

  function payloadForYarn(yarn,queue){
    if(!yarn)return null;
    const direct=queue.find(item=>item?.capture_id&&item.capture_id===yarn.sourceCaptureId)?.payload;
    if(direct)return direct;
    return queue.find(item=>{
      const p=item?.payload||{};
      return p.targetType==='yarn'&&normalize(p.yarnName)===normalize(yarn.name)&&(!p.yarnCode||!yarn.code||normalize(p.yarnCode)===normalize(yarn.code));
    })?.payload||null;
  }
  function applyPayloadFields(state,queue){
    if(!Array.isArray(state?.yarns))return state;
    for(const yarn of state.yarns){
      const payload=payloadForYarn(yarn,queue);if(!payload)continue;
      if(payload.preSpinningPreparation)yarn.preSpinningPreparation=normalizePre(payload.preSpinningPreparation);
      if(payload.spinningMethod)yarn.spinningMethod=normalizeSpin(payload.spinningMethod);
      if(payload.spinningMethodRaw)yarn.spinningMethodRaw=normalize(payload.spinningMethodRaw);
    }
    return state;
  }
  function formFields(doc){
    const form=doc?.getElementById('yarnForm');if(!form||!form.dataset.kcYarnProcessFields)return null;
    return{
      id:normalize(doc.getElementById('yarnId')?.value),
      supplier:normalize(doc.getElementById('yarnSupplier')?.value),
      name:normalize(doc.getElementById('yarnName')?.value),
      code:normalize(doc.getElementById('yarnCode')?.value),
      preSpinningPreparation:normalizePre(doc.getElementById('yarnPreSpinningPreparation')?.value||'unconfirmed'),
      spinningMethod:normalizeSpin(doc.getElementById('yarnFinalSpinningMethod')?.value||'unconfirmed'),
      spinningMethodRaw:normalize(doc.getElementById('yarnSpinningMethodRaw')?.value)
    };
  }
  function applyFormFields(state,fields){
    if(!fields||!Array.isArray(state?.yarns))return state;
    let yarn=fields.id?state.yarns.find(row=>row.id===fields.id):null;
    if(!yarn)yarn=state.yarns.find(row=>normalize(row.supplier)===fields.supplier&&normalize(row.name)===fields.name&&(!fields.code||normalize(row.code)===fields.code));
    if(!yarn)return state;
    yarn.preSpinningPreparation=fields.preSpinningPreparation;
    yarn.spinningMethod=fields.spinningMethod;
    yarn.spinningMethodRaw=fields.spinningMethodRaw;
    return state;
  }
  function hookStateWrites(win){
    if(!win?.Storage?.prototype||win.Storage.prototype.__kcYarnProcessHooked)return;
    const proto=win.Storage.prototype,original=proto.setItem;
    Object.defineProperty(proto,'__kcYarnProcessHooked',{value:true,configurable:true});
    proto.setItem=function(key,value){
      if(key===V04_KEY&&typeof value==='string'){
        try{
          const state=JSON.parse(value);
          const queue=readJson(win.localStorage,HANDOFF_KEY,[]);
          applyPayloadFields(state,queue);
          applyFormFields(state,formFields(win.document));
          value=JSON.stringify(state);
        }catch(error){console.warn('[KC] yarn process master state hook skipped',error)}
      }
      return original.call(this,key,value);
    };
  }

  function stateFrom(win){return readJson(win.localStorage,V04_KEY,{yarns:[]})}
  function yarnFromForm(win){
    const state=stateFrom(win),id=normalize(win.document.getElementById('yarnId')?.value);
    if(id)return state.yarns?.find(row=>row.id===id)||null;
    const supplier=normalize(win.document.getElementById('yarnSupplier')?.value),name=normalize(win.document.getElementById('yarnName')?.value),code=normalize(win.document.getElementById('yarnCode')?.value);
    return state.yarns?.find(row=>normalize(row.supplier)===supplier&&normalize(row.name)===name&&(!code||normalize(row.code)===code))||null;
  }
  function enhanceYarnForm(win){
    const doc=win.document,form=doc.getElementById('yarnForm'),structure=doc.getElementById('yarnStructure');
    if(!form||!structure||form.dataset.kcYarnProcessFields==='1')return;
    form.dataset.kcYarnProcessFields='1';
    const yarn=yarnFromForm(win)||{};
    const container=structure.closest('.field')?.parentNode;if(!container)return;
    const structureField=structure.closest('.field');
    const block=doc.createElement('div');block.className='field';
    block.innerHTML=`<label for="yarnPreSpinningPreparation">前紡・綿処理</label><select id="yarnPreSpinningPreparation">${optionsHtml(PRE_OPTIONS,normalizePre(yarn.preSpinningPreparation||'unconfirmed'))}</select>`;
    container.insertBefore(block,structureField.nextSibling);
    const spin=doc.createElement('div');spin.className='field';
    spin.innerHTML=`<label for="yarnFinalSpinningMethod">最終紡績方式</label><select id="yarnFinalSpinningMethod">${optionsHtml(SPIN_OPTIONS,normalizeSpin(yarn.spinningMethod||'unconfirmed'))}</select>`;
    container.insertBefore(spin,block.nextSibling);
    const raw=doc.createElement('div');raw.className='field';
    raw.innerHTML=`<label for="yarnSpinningMethodRaw">紡績方式 原文・旧値</label><input id="yarnSpinningMethodRaw" value="${esc(yarn.spinningMethodRaw||'')}" placeholder="Siro / Supplier原文">`;
    container.insertBefore(raw,spin.nextSibling);
  }
  function enhanceYarnDetail(win){
    const doc=win.document,body=doc.getElementById('detailBody'),title=normalize(doc.getElementById('detailTitle')?.textContent);
    if(!body||body.dataset.kcYarnProcessDetail===title||!title.includes('｜'))return;
    const state=stateFrom(win);const yarn=state.yarns?.find(row=>title===normalize(`${row.supplier}｜${row.name}`));if(!yarn)return;
    const dl=body.querySelector('dl.detail-list');if(!dl)return;
    body.dataset.kcYarnProcessDetail=title;
    for(const [label,value] of [
      ['前紡・綿処理',PRE_LABEL[normalizePre(yarn.preSpinningPreparation)]||'未確認'],
      ['最終紡績方式',SPIN_LABEL[normalizeSpin(yarn.spinningMethod)]||'未確認'],
      ['紡績方式 原文・旧値',normalize(yarn.spinningMethodRaw)||'—']
    ]){const dt=doc.createElement('dt');dt.textContent=label;const dd=doc.createElement('dd');dd.textContent=value;dl.append(dt,dd)}
  }
  function exportProcessCsv(win){
    const rows=stateFrom(win).yarns||[];if(!rows.length)return;
    const cols=['id','supplier','name','code','displayCount','structure','preSpinningPreparation','spinningMethod','spinningMethodRaw','composition','gauge','status','sourceUrl'];
    const q=v=>`"${String(v??'').replaceAll('"','""')}"`;
    const text='\uFEFF'+[cols.join(','),...rows.map(row=>cols.map(c=>q(row[c])).join(','))].join('\r\n');
    const blob=new Blob([text],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=win.document.createElement('a');
    a.href=url;a.download=`kc_yarn_process_fields_${new Date().toISOString().slice(0,10)}.csv`;win.document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);
  }
  function enhanceV04(win){
    if(!win?.document)return;hookStateWrites(win);
    const doc=win.document;
    const scan=()=>{enhanceYarnForm(win);enhanceYarnDetail(win)};
    new win.MutationObserver(scan).observe(doc.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['class']});
    doc.getElementById('exportCsv')?.addEventListener('click',()=>exportProcessCsv(win));
    scan();
  }
  function attachReviewFrame(reviewWin){
    if(!reviewWin?.document)return;hookStateWrites(reviewWin);
    const nested=reviewWin.document.getElementById('v04Frame');if(!nested)return;
    const apply=()=>{try{enhanceV04(nested.contentWindow)}catch(error){console.warn('[KC] V04 yarn process overlay unavailable',error)}};
    nested.addEventListener('load',apply);apply();
  }
  function install(){
    const frame=document.getElementById('contentFrame');if(!frame)return;
    const apply=()=>{try{if(String(frame.getAttribute('src')||'').includes('index-current'))attachReviewFrame(frame.contentWindow)}catch(error){console.warn('[KC] Human Review yarn process overlay unavailable',error)}};
    frame.addEventListener('load',apply);apply();
  }

  window.KCYarnProcessMaster={normalizePre,normalizeSpin,applyPayloadFields,applyFormFields};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
