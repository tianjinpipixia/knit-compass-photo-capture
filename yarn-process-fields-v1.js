(()=>{
  'use strict';

  const DB_NAME='kc_independent_photo_capture_v1_0';
  const CONTRACT_VERSION='1.2.0';
  const PRE_OPTIONS=[
    ['unconfirmed','未確認'],['carded','カード'],['combed','コーマ'],['semi_combed','セミコーマ'],['other','その他']
  ];
  const SPIN_OPTIONS=[
    ['unconfirmed','未確認'],['ring','リング'],['compact','コンパクト'],['mvs_vortex','MVS・VORTEX'],['air_jet','エアジェット'],['oe_rotor','OE・ローター'],['other','その他（原文保持）']
  ];

  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const normalize=value=>String(value||'').trim().normalize('NFKC');
  function normalizePre(value){
    const original=normalize(value);const raw=original.toLowerCase();
    if(['unconfirmed','carded','combed','semi_combed','other'].includes(original))return original;
    if(!raw||raw==='unknown'||raw==='未確認')return'unconfirmed';
    if(/semi.?combed|半精梳|セミコーマ/.test(raw))return'semi_combed';
    if(/combed|精梳|コーマ/.test(raw))return'combed';
    if(/carded|普梳|カード/.test(raw))return'carded';
    return'other';
  }
  function normalizeSpin(value){
    const original=normalize(value);const raw=original.toLowerCase();
    if(['unconfirmed','ring','compact','mvs_vortex','air_jet','oe_rotor','other'].includes(original))return original;
    if(!raw||raw==='unknown'||raw==='未確認')return'unconfirmed';
    if(/compact|紧密纺|コンパクト/.test(raw))return'compact';
    if(/mvs|vortex|涡流纺|渦流/.test(raw))return'mvs_vortex';
    if(/air.?jet|喷气纺|エアジェット/.test(raw))return'air_jet';
    if(/open.?end|\boe\b|rotor|气流纺|转杯纺|ローター/.test(raw))return'oe_rotor';
    if(/^ring$|环锭纺|リング/.test(raw))return'ring';
    return'other';
  }
  function optionsHtml(options,selected){return options.map(([value,label])=>`<option value="${value}" ${value===selected?'selected':''}>${esc(label)}</option>`).join('')}
  function currentForm(){return document.getElementById('capture')}
  function formProcessValues(){
    const form=currentForm();
    if(!form)return null;
    const pre=normalizePre(form.elements.preSpinningPreparation?.value||'unconfirmed');
    const selected=form.elements.spinningMethod?.value||'unconfirmed';
    const spin=normalizeSpin(selected);
    let raw=normalize(form.elements.spinningMethodRaw?.value||'');
    if(!raw&&spin==='other'&&selected&&!['other','unconfirmed'].includes(selected))raw=normalize(selected);
    return{preSpinningPreparation:pre,spinningMethod:spin,spinningMethodRaw:raw};
  }
  function augmentEventRow(value){
    if(!value?.snapshot)return value;
    const fields=formProcessValues();if(!fields)return value;
    value.snapshot.dataContractVersion=CONTRACT_VERSION;
    value.snapshot.preSpinningPreparation=fields.preSpinningPreparation;
    value.snapshot.spinningMethod=fields.spinningMethod;
    value.snapshot.spinningMethodRaw=fields.spinningMethodRaw;
    return value;
  }

  const originalAdd=IDBObjectStore.prototype.add;
  IDBObjectStore.prototype.add=function(value,key){
    if(this.name==='events')augmentEventRow(value);
    return originalAdd.call(this,value,key);
  };
  const originalPut=IDBObjectStore.prototype.put;
  IDBObjectStore.prototype.put=function(value,key){
    if(this.name==='events')augmentEventRow(value);
    return originalPut.call(this,value,key);
  };

  function latestSnapshotForForm(form){
    return new Promise(resolve=>{
      const request=indexedDB.open(DB_NAME);
      request.onerror=()=>resolve(null);
      request.onsuccess=()=>{
        const db=request.result;
        if(!db.objectStoreNames.contains('events')){db.close();resolve(null);return}
        const tx=db.transaction('events','readonly');
        const req=tx.objectStore('events').getAll();
        req.onerror=()=>{db.close();resolve(null)};
        req.onsuccess=()=>{
          const targetId=normalize(form.elements.targetId?.value);
          const yarnName=normalize(form.elements.yarnName?.value);
          const yarnCode=normalize(form.elements.yarnCode?.value);
          const source=normalize(form.elements.sourceOrganizationName?.value);
          const events=(req.result||[]).filter(row=>{
            const s=row?.snapshot||{};
            if(targetId&&normalize(s.targetId)===targetId)return true;
            if(yarnName&&normalize(s.yarnName)===yarnName){
              if(yarnCode&&normalize(s.yarnCode)!==yarnCode)return false;
              if(source&&normalize(s.sourceOrganizationName||s.supplier)!==source)return false;
              return true;
            }
            return false;
          }).sort((a,b)=>String(b.updatedAt||'').localeCompare(String(a.updatedAt||'')));
          const snapshot=events[0]?.snapshot||null;db.close();resolve(snapshot);
        };
      };
    });
  }

  async function enhanceForm(form){
    if(form.dataset.kcYarnProcessFields==='1')return;
    const spinSelect=form.elements.spinningMethod;
    if(!spinSelect)return;
    form.dataset.kcYarnProcessFields='1';
    const originalSpin=normalize(spinSelect.value);
    const normalizedSpin=normalizeSpin(originalSpin);
    spinSelect.innerHTML=optionsHtml(SPIN_OPTIONS,normalizedSpin);
    const spinLabel=spinSelect.closest('label');
    if(spinLabel){
      const preLabel=document.createElement('label');
      preLabel.innerHTML=`前紡・綿処理<select name="preSpinningPreparation">${optionsHtml(PRE_OPTIONS,'unconfirmed')}</select>`;
      spinLabel.parentNode.insertBefore(preLabel,spinLabel);
      const rawLabel=document.createElement('label');
      rawLabel.innerHTML=`紡績方式 原文・旧値<input name="spinningMethodRaw" value="${esc(normalizedSpin==='other'?originalSpin:'')}" placeholder="例：Siro / Supplier原文">`;
      spinLabel.parentNode.insertBefore(rawLabel,spinLabel.nextSibling);
      spinLabel.childNodes[0].nodeValue='最終紡績方式';
    }
    const existing=await latestSnapshotForForm(form);
    if(!document.body.contains(form))return;
    if(existing){
      form.elements.preSpinningPreparation.value=normalizePre(existing.preSpinningPreparation||'unconfirmed');
      const storedSpin=normalizeSpin(existing.spinningMethod||originalSpin||'unconfirmed');
      form.elements.spinningMethod.value=storedSpin;
      form.elements.spinningMethodRaw.value=normalize(existing.spinningMethodRaw||(storedSpin==='other'?existing.spinningMethod||originalSpin:''));
    }
  }

  const observer=new MutationObserver(()=>{const form=currentForm();if(form)enhanceForm(form)});
  observer.observe(document.documentElement,{childList:true,subtree:true});
  if(currentForm())enhanceForm(currentForm());

  window.KCYarnProcessFields={normalizePre,normalizeSpin,formProcessValues};
})();
