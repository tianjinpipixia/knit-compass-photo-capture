(()=>{
  'use strict';

  const BATCH_URL='../data/manual-intake/2026-08-18-american-holic-products-batch8.json';
  const MARKER='kcOwnerObservedProducts';
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const normalize=value=>String(value??'').toLowerCase().replace(/[,、／\\/%％・()（）\-]+/g,' ').replace(/\s+/g,' ').trim();

  const candidatesPromise=fetch(BATCH_URL,{cache:'no-store'})
    .then(response=>{if(!response.ok)throw new Error(`HTTP ${response.status}`);return response.json()})
    .then(data=>(Array.isArray(data.items)?data.items:[])
      .filter(item=>item?.review_status==='PENDING'&&item?.payload?.targetType==='product')
      .map(item=>{
        const payload=item.payload||{};
        const functions=(payload.functionalProperties||[]).map(row=>row?.name).filter(Boolean);
        return {
          handoffId:item.handoff_id||'',
          reviewStatus:item.review_status||'PENDING',
          brand:payload.brandName||'',
          name:payload.productName||'',
          productCode:payload.productCode||'',
          composition:payload.compositionRaw||'',
          country:payload.countryOfOrigin||'',
          color:payload.observedColor||'',
          size:payload.observedSize||'',
          price:payload.observedPriceYenTaxIncluded||'',
          observedOn:payload.observedOn||'',
          functions,
          notes:payload.notes||'',
          evidenceId:payload.evidenceId||''
        };
      })
      .filter(row=>row.brand&&row.name&&row.productCode));

  function matches(row,query){
    if(!query)return true;
    const hay=normalize([
      row.brand,row.name,row.productCode,row.composition,row.country,row.color,row.size,
      row.price,row.observedOn,row.functions.join(' '),row.notes
    ].join(' '));
    return normalize(query).split(' ').filter(Boolean).every(term=>hay.includes(term));
  }

  function install(appDoc,reviewDoc,candidates){
    if(!appDoc?.documentElement||appDoc.documentElement.dataset[MARKER]==='1')return;
    const productSearch=appDoc.getElementById('productSearch');
    const workflowFilter=appDoc.getElementById('workflowFilter');
    const brandFilter=appDoc.getElementById('brandFilter');
    const workflowBoard=appDoc.getElementById('workflowBoard');
    if(!productSearch||!workflowFilter||!brandFilter||!workflowBoard)return;
    appDoc.documentElement.dataset[MARKER]='1';

    const style=appDoc.createElement('style');
    style.textContent=`
      .kc-owner-observed-product{border-color:#9eb8c8;background:#fbfdff}
      .kc-owner-observed-product .kc-observed-tags{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:5px}
      .kc-owner-observed-product .kc-observed-tag{display:inline-flex;align-items:center;border-radius:999px;padding:3px 7px;font-size:8px;font-weight:900;background:#eaf3fb;color:#315d86}
      .kc-owner-observed-product .kc-pending-tag{background:#fff5df;color:#8a5d12}
      .kc-owner-observed-product details{margin-top:7px;border-top:1px solid #d6dfdb;padding-top:6px}
      .kc-owner-observed-product summary{cursor:pointer;font-size:9px;font-weight:900;color:#235c56}
      .kc-owner-observed-detail{display:grid;gap:3px;margin-top:6px;font-size:9px;color:#5d6d69}
      .kc-owner-observed-badge{margin-left:5px;background:#eaf3fb;color:#315d86}
    `;
    appDoc.head.append(style);

    const candidateBrands=new Set(candidates.map(row=>row.brand));
    let stickyCandidateBrand='';
    const ensureBrandOptions=()=>{
      for(const brand of candidateBrands){
        if(![...brandFilter.options].some(option=>option.value===brand))brandFilter.add(new Option(`${brand}（現物候補）`,brand));
      }
      if(stickyCandidateBrand&&candidateBrands.has(stickyCandidateBrand))brandFilter.value=stickyCandidateBrand;
    };
    brandFilter.addEventListener('change',()=>{stickyCandidateBrand=candidateBrands.has(brandFilter.value)?brandFilter.value:''},true);

    const nativeMasterHasCode=code=>{
      const target=normalize(code);
      if(!target)return false;
      return [...workflowBoard.querySelectorAll('.mini-product:not(.kc-owner-observed-product)')]
        .some(card=>normalize(card.textContent).includes(target));
    };

    const selectedRows=()=>{
      ensureBrandOptions();
      const query=productSearch.value.trim();
      const workflow=workflowFilter.value;
      const brand=brandFilter.value;
      if(workflow&&workflow!=='STORE_CONFIRMED')return [];
      return candidates.filter(row=>(!brand||row.brand===brand)&&matches(row,query)&&!nativeMasterHasCode(row.productCode));
    };

    let scheduled=false;
    const scheduleRender=()=>{
      if(scheduled)return;
      scheduled=true;
      setTimeout(()=>{scheduled=false;render()},0);
    };

    function render(){
      ensureBrandOptions();
      workflowBoard.querySelectorAll('.kc-owner-observed-product,.kc-owner-observed-badge').forEach(node=>node.remove());
      const rows=selectedRows();
      if(!rows.length)return;
      const column=[...workflowBoard.querySelectorAll('.workflow-column')]
        .find(node=>normalize(node.querySelector('h3')?.textContent).startsWith(normalize('現物確認')));
      if(!column)return;
      const heading=column.querySelector('h3');
      if(heading){
        const badge=appDoc.createElement('span');
        badge.className='tag kc-owner-observed-badge';
        badge.textContent=`+${rows.length} 現物候補`;
        heading.append(badge);
      }
      const fragment=appDoc.createDocumentFragment();
      for(const row of rows){
        const card=appDoc.createElement('article');
        card.className='mini-product kc-owner-observed-product';
        card.dataset.productCode=row.productCode;
        const price=row.price?`税込${Number(row.price).toLocaleString('ja-JP')}円（観測）`:'';
        card.innerHTML=`
          <div class="kc-observed-tags"><span class="kc-observed-tag">現物タグ確認</span><span class="kc-observed-tag kc-pending-tag">Human Review前</span></div>
          <strong>${esc(row.brand)}｜${esc(row.name)}</strong>
          <span>${esc([row.productCode,row.composition].filter(Boolean).join(' ／ '))}</span>
          <details>
            <summary>詳細を表示</summary>
            <div class="kc-owner-observed-detail">
              <div><b>品番:</b> ${esc(row.productCode)}</div>
              <div><b>混率:</b> ${esc(row.composition||'—')}</div>
              <div><b>機能訴求:</b> ${esc(row.functions.join('、')||'—')}</div>
              <div><b>色 / サイズ:</b> ${esc([row.color,row.size].filter(Boolean).join(' / ')||'—')}</div>
              <div><b>原産国:</b> ${esc(row.country||'—')}</div>
              <div><b>価格:</b> ${esc(price||'—')}</div>
              <div><b>現物確認日:</b> ${esc(row.observedOn||'—')}</div>
              <div><b>状態:</b> PENDING（正式マスター未反映）</div>
            </div>
          </details>
          <div class="btn-row"><button class="btn secondary small kc-open-human-review" type="button">Human Reviewを開く</button></div>`;
        card.querySelector('.kc-open-human-review')?.addEventListener('click',()=>reviewDoc?.getElementById('openInbox')?.click());
        fragment.append(card);
      }
      column.append(fragment);
    }

    productSearch.addEventListener('input',scheduleRender);
    workflowFilter.addEventListener('change',scheduleRender);
    brandFilter.addEventListener('change',scheduleRender);
    const observer=new MutationObserver(()=>{
      const expected=selectedRows().length;
      const actual=workflowBoard.querySelectorAll('.kc-owner-observed-product').length;
      if(expected!==actual)scheduleRender();
    });
    observer.observe(workflowBoard,{childList:true,subtree:true});
    ensureBrandOptions();
    render();
  }

  function wireReviewFrame(reviewFrame,candidates){
    const tryInstall=()=>{
      const reviewDoc=reviewFrame.contentDocument;
      if(!reviewDoc)return;
      const appFrame=reviewDoc.getElementById('v04Frame');
      if(!appFrame){setTimeout(tryInstall,80);return}
      const installNow=()=>{
        const appDoc=appFrame.contentDocument;
        if(!appDoc)return;
        if(appDoc.readyState==='loading'){setTimeout(installNow,50);return}
        install(appDoc,reviewDoc,candidates);
      };
      appFrame.addEventListener('load',installNow);
      installNow();
    };
    tryInstall();
  }

  candidatesPromise.then(candidates=>{
    if(!candidates.length)return;
    const contentFrame=document.getElementById('contentFrame');
    if(!contentFrame)return;
    const wire=()=>wireReviewFrame(contentFrame,candidates);
    contentFrame.addEventListener('load',wire);
    if(contentFrame.contentDocument?.readyState==='complete')wire();
  }).catch(error=>console.warn('Owner-observed product candidates could not be loaded:',error));
})();

(()=>{
  'use strict';
  const sources=['./brand-diff-auto-intake.js?v=1.0.0','./yarn-process-master-v1.js?v=1.0.0'];
  for(const src of sources){
    if(document.querySelector(`script[data-kc-extension="${src}"]`))continue;
    const script=document.createElement('script');
    script.src=src;script.dataset.kcExtension=src;script.defer=true;document.head.appendChild(script);
  }
})();
