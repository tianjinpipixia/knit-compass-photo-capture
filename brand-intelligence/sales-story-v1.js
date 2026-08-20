(()=>{
  'use strict';
  const V04_KEY='kc_independent_practical_v0_4';
  const FRAMEWORK_URL='./data/sales-story/sales-story-framework.json?v=1.0.0';
  const CONFIRMED=new Set(['document_confirmed','test_confirmed','confirmed']);
  let frameworkCache=null;
  const text=value=>String(value??'').trim();
  const arr=value=>Array.isArray(value)?value:[];
  const state=()=>{try{return JSON.parse(localStorage.getItem(V04_KEY)||'{}')}catch{return{}}};
  const namedConfirmed=items=>arr(items).filter(item=>CONFIRMED.has(item?.status||item?.claimStatus||item?.verificationStatus)).map(item=>item.name||item.code).filter(Boolean);
  const find=(rows,id)=>arr(rows).find(row=>row.id===id||row.commonId===id);
  async function framework(){
    if(frameworkCache)return frameworkCache;
    const response=await fetch(FRAMEWORK_URL,{cache:'no-store'});
    if(!response.ok)throw new Error(`Sales Story framework unavailable: HTTP ${response.status}`);
    frameworkCache=await response.json();
    return frameworkCache;
  }
  function evidenceLines(template){
    return arr(template.market_evidence).map(row=>{
      const subject=[row.brand,row.product,row.supplier,row.spec].filter(Boolean).join('｜');
      const facts=[row.product_code,row.season,row.composition,row.status].filter(Boolean).join(' / ');
      return `- ${subject}${facts?` — ${facts}`:''}`;
    });
  }
  async function generate({templateId,materialId='',yarnId='',productId='',customer='',notes=''}={}){
    const f=await framework();
    const template=arr(f.templates).find(row=>row.id===templateId);
    if(!template)throw new Error('Sales Story template not found');
    const s=state();
    const material=find(s.materials,materialId);
    const yarn=find(s.yarns,yarnId);
    const product=find(s.products,productId);
    const functions=[...new Set([
      ...namedConfirmed(material?.functionalProperties),
      ...namedConfirmed(yarn?.functionalProperties),
      ...namedConfirmed(product?.functionalProperties)
    ])];
    const sustainable=[...new Set([
      ...namedConfirmed(material?.sustainableAttributes),
      ...namedConfirmed(yarn?.sustainableAttributes),
      ...namedConfirmed(product?.sustainableAttributes)
    ])];
    const risks=[];
    if(material&&material.verificationStatus!=='confirmed')risks.push(`素材 ${material.name||material.id} は ${material.verificationStatus||'未確認'}。`);
    if(yarn&&yarn.verificationStatus!=='confirmed'&&yarn.status!=='CONFIRMED')risks.push(`糸 ${yarn.name||yarn.id} は正式確認前。`);
    if(functions.length===0)risks.push('機能は確認済み根拠がないためSales Storyでは断定しない。');
    const yarnProcess=yarn?[
      yarn.cottonPreparation?`前紡: ${yarn.cottonPreparation}`:'',
      yarn.finalSpinningMethod?`最終紡績: ${yarn.finalSpinningMethod}`:'',
      yarn.structure?`構造: ${yarn.structure}`:''
    ].filter(Boolean).join(' / '):'';
    const selection=[
      material?`素材: ${[material.tradeName,material.name,material.composition].filter(Boolean).join(' / ')}`:'',
      yarn?`糸: ${[yarn.supplier,yarn.name,yarn.displayCount,yarn.composition].filter(Boolean).join(' / ')}`:'',
      yarnProcess,
      product?`商品起点: ${[product.brand,product.name,product.productNumber].filter(Boolean).join(' / ')}`:''
    ].filter(Boolean);
    return [
      `# Sales Story — ${template.title}`,
      customer?`\n**対象:** ${customer}`:'',
      `\n## Market Signal\n${template.signal}`,
      `\n## Market Evidence\n${evidenceLines(template).join('\n')||'- 追加確認待ち'}`,
      `\n## 提案対象\n${selection.map(v=>`- ${v}`).join('\n')||'- 素材・糸を選択してください'}`,
      `\n## 確認済み機能\n${functions.map(v=>`- ${v}`).join('\n')||'- なし（未確認は記載しない）'}`,
      sustainable.length?`\n## サステナブル根拠\n${sustainable.map(v=>`- ${v}`).join('\n')}`:'',
      `\n## Sales Angle\n${arr(template.sales_angle).map(v=>`- ${v}`).join('\n')}`,
      `\n## 必須確認\n${arr(template.required_checks).map(v=>`- ${v}`).join('\n')}`,
      `\n## リスク・境界\n${risks.map(v=>`- ${v}`).join('\n')||'- 現時点で追加リスクなし'}`,
      notes?`\n## メモ\n${notes}`:'',
      `\n> 販売数量は根拠資料がある場合のみ記載し、推定しない。競合商品は市場根拠として扱い、仕様コピーの根拠にはしない。`
    ].filter(Boolean).join('\n');
  }
  window.KnitCompassSalesStory=Object.freeze({framework,generate});
})();
