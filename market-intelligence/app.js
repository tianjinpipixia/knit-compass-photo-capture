(()=>{
  'use strict';
  const STORAGE_KEY='kc_market_intelligence_observations_v1';
  const SCHEMA_VERSION='1.1.0';
  const PROPOSAL_URL='../data/brand-md-monitoring/latest-material-proposals.json';
  const LATEST_MD_URL='../data/brand-md-monitoring/latest.json';
  const CATALOG_URLS=['../data/yarn-catalog/mz100-catalog-3000.json','../data/yarn-catalog/mz100-catalog-2000.json'];
  const SIX_MATERIALS=[
    {id:'COTTON',label:'綿',hint:'中国綿花・紡績原料'},
    {id:'WOOL',label:'ウール',hint:'中国向け羊毛・毛条'},
    {id:'LINEN',label:'麻',hint:'亜麻・苧麻など（品質を明記）'},
    {id:'NYLON',label:'ナイロン',hint:'ナイロン原料・フィラメント'},
    {id:'POLYESTER',label:'ポリエステル',hint:'バージンポリエステル'},
    {id:'RECYCLED_POLYESTER',label:'再生ポリエステル',hint:'再生由来・認証範囲を明記'}
  ];
  const MATERIAL_IDS=new Set(SIX_MATERIALS.map(row=>row.id));
  const VERIFIED_EVIDENCE=new Set(['SOURCE_CHECKED','SUPPLIER_CONFIRMED']);
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const normalize=value=>String(value||'').toLowerCase().normalize('NFKC').replace(/[,、／/%％・()（）\-]+/g,' ').replace(/\s+/g,' ').trim();
  const nowIso=()=>new Date().toISOString();
  const localDate=()=>{const date=new Date();date.setMinutes(date.getMinutes()-date.getTimezoneOffset());return date.toISOString().slice(0,10)};
  const newId=()=>`MI-${localDate().replaceAll('-','')}-${Date.now().toString(36).toUpperCase()}-${crypto.getRandomValues(new Uint16Array(1))[0].toString(36).toUpperCase()}`;
  const materialLabels=Object.fromEntries(SIX_MATERIALS.map(row=>[row.id,row.label]));
  const evidenceLabels={SOURCE_CHECKED:'原資料確認済み',SUPPLIER_CONFIRMED:'Supplier確認済み'};
  const directionLabels={UNKNOWN:'不明・未比較',UP:'上昇',FLAT:'横ばい',DOWN:'下落',VOLATILE:'変動大'};

  function emptyState(){return{format:'KC_MARKET_INTELLIGENCE_EXPORT',schema_version:SCHEMA_VERSION,observations:[]}}
  function loadState(){try{const parsed=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');return parsed&&Array.isArray(parsed.observations)?{...emptyState(),...parsed}:emptyState()}catch{return emptyState()}}
  function saveState(state){localStorage.setItem(STORAGE_KEY,JSON.stringify({...state,format:'KC_MARKET_INTELLIGENCE_EXPORT',schema_version:SCHEMA_VERSION,updated_at:nowIso()}))}
  function validUrl(value){if(!value)throw new Error('確認済みソースの根拠URLを入力してください。');const url=new URL(value);if(!['http:','https:'].includes(url.protocol))throw new Error('根拠URLは http または https を使用してください。');return url.href}
  function setMessage(text,error=false){const target=$('formMessage');target.textContent=text;target.classList.toggle('error',error)}
  function verifiedChina(row){return MATERIAL_IDS.has(row.material)&&row.country_code==='CN'&&row.market_scope==='CHINA'&&VERIFIED_EVIDENCE.has(row.evidence_status)&&Boolean(row.source_url)}
  function quoteText(row){return[row.quote,row.currency,row.unit?`/ ${row.unit}`:''].filter(Boolean).join(' ')||'定性観測'}

  function renderCategories(rows){
    $('categoryGrid').innerHTML=SIX_MATERIALS.map(material=>{
      const latest=rows.filter(row=>row.material===material.id).sort((a,b)=>`${b.observed_on||''}${b.created_at||''}`.localeCompare(`${a.observed_on||''}${a.created_at||''}`))[0];
      if(!latest)return`<article class="category-card"><div class="tag-row"><span class="tag">${esc(material.id)}</span><span class="tag pending">未登録</span></div><h3>${esc(material.label)}</h3><div class="latest">確認済み観測なし</div><div class="meta">${esc(material.hint)}\n推定値で補完しません。</div></article>`;
      return`<article class="category-card"><div class="tag-row"><span class="tag safe">${esc(evidenceLabels[latest.evidence_status])}</span><span class="tag">CN</span></div><h3>${esc(material.label)}</h3><div class="latest">${esc(quoteText(latest))}</div><div class="meta">${esc(latest.observed_on)}／${esc(latest.market)}${latest.indicator?`\n${esc(latest.indicator)}`:''}\n自動換算なし</div><a class="source" href="${esc(latest.source_url)}" target="_blank" rel="noopener">${esc(latest.source_name)}を確認</a></article>`;
    }).join('');
  }

  function render(){
    const state=loadState();
    const query=normalize($('recordSearch').value);
    const rows=state.observations.filter(verifiedChina).sort((a,b)=>String(b.created_at||'').localeCompare(String(a.created_at||'')));
    $('totalCount').textContent=rows.length;
    $('pendingCount').textContent=rows.filter(row=>row.review_status==='PENDING_HUMAN_REVIEW').length;
    $('verifiedCount').textContent=rows.filter(row=>Boolean(row.source_url)).length;
    $('materialCount').textContent=`${new Set(rows.map(row=>row.material)).size} / 6`;
    renderCategories(rows);
    const visible=rows.filter(row=>!query||normalize([row.observation_id,materialLabels[row.material],row.market,row.indicator,row.source_name,row.quote,row.currency,row.unit,row.direction,row.notes].join(' ')).includes(query));
    $('recordList').innerHTML=visible.length?visible.map(row=>`<article class="record"><div><div class="tag-row"><span class="tag pending">PENDING HUMAN REVIEW</span><span class="tag">${esc(directionLabels[row.direction]||row.direction)}</span><span class="tag safe">${esc(evidenceLabels[row.evidence_status])}</span></div><h3>${esc(materialLabels[row.material])}｜${esc(row.market)}</h3><p>${esc(row.observation_id)}／${esc(row.observed_on)}${row.indicator?`\n${esc(row.indicator)}`:''}\n情報源: ${esc(row.source_name)}${row.notes?`\n${esc(row.notes)}`:''}</p></div><div class="quote"><strong>${esc(quoteText(row))}</strong><span>自動換算なし</span><a href="${esc(row.source_url)}" target="_blank" rel="noopener">出典</a></div></article>`).join(''):'<div class="empty">条件に一致する確認済み相場観測はありません。</div>';
  }

  function observationFromForm(form){
    const data=new FormData(form);
    const material=String(data.get('material')||'');
    const evidenceStatus=String(data.get('evidenceStatus')||'');
    if(!MATERIAL_IDS.has(material))throw new Error('比較対象の6原料から選択してください。');
    if(!VERIFIED_EVIDENCE.has(evidenceStatus))throw new Error('原資料確認済みまたはSupplier確認済みだけを保存できます。');
    return{
      observation_id:newId(),record_type:'RAW_MATERIAL_MARKET_OBSERVATION',review_status:'PENDING_HUMAN_REVIEW',publication_status:'HOLD',
      country_code:'CN',market_scope:'CHINA',observed_on:String(data.get('observedOn')||''),material,
      market:String(data.get('market')||'').trim(),indicator:String(data.get('indicator')||'').trim(),quote:String(data.get('quote')||'').trim(),
      currency:String(data.get('currency')||'').trim().toUpperCase(),unit:String(data.get('unit')||'').trim(),direction:String(data.get('direction')||'UNKNOWN'),
      evidence_status:evidenceStatus,source_name:String(data.get('sourceName')||'').trim(),source_url:validUrl(String(data.get('sourceUrl')||'').trim()),
      value_policy:'SOURCE_AS_WRITTEN_NO_CONVERSION',notes:String(data.get('notes')||'').trim(),created_at:nowIso()
    };
  }

  async function fetchJson(url){const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw new Error(`${url}: HTTP ${response.status}`);return response.json()}
  async function fetchCatalog(){let lastError;for(const url of CATALOG_URLS){try{const data=await fetchJson(url);if(!Array.isArray(data.records))throw new Error(`${url}: records missing`);return data.records}catch(error){lastError=error}}throw lastError||new Error('catalog unavailable')}
  function proposalMatches(catalog,proposal){
    return catalog.map(row=>{const hay=normalize([row.name,row.count_display,row.composition_raw,row.listed_supplier].join(' '));const score=(proposal.candidate_terms||[]).filter(term=>hay.includes(normalize(term))).length;return{row,score}}).filter(match=>match.score>=(proposal.minimum_term_matches||1)&&match.row.master_status==='NOT_PROMOTED').sort((a,b)=>b.score-a.score||Number(Boolean(b.row.count_display))+Number(Boolean(b.row.composition_raw))-Number(Boolean(a.row.count_display))-Number(Boolean(a.row.composition_raw)));
  }
  function candidateHtml(matches){return matches.slice(0,3).map(({row})=>`<div class="candidate"><span><b>${esc(row.name)}</b><br>${esc(row.count_display||'番手要確認')}／${esc(row.composition_raw||'混率要確認')}</span><span>正式登録前</span></div>`).join('')||'<div class="candidate"><span>条件一致候補なし</span><span>要確認</span></div>'}
  async function loadMdFlow(){
    try{
      const[latest,proposalData,catalog]=await Promise.all([fetchJson(LATEST_MD_URL),fetchJson(PROPOSAL_URL),fetchCatalog()]);
      const observedDate=new Date(`${latest.observed_date}T00:00:00+09:00`);
      const ageDays=Math.max(0,Math.floor((Date.now()-observedDate.getTime())/86400000));
      const proposalDate=String(proposalData.observed_date||'');
      const freshnessOk=ageDays<=1&&proposalDate===latest.observed_date;
      const freshnessHtml=`<div class="notice ${freshnessOk?'':'warn'}"><strong>${freshnessOk?'日次観測は最新です':'日次観測または素材提案の更新が必要です'}</strong> 観測日 ${esc(latest.observed_date)}／素材提案 ${esc(proposalDate||'未設定')}。古い情報を最新として扱いません。</div>`;
      queueMicrotask(()=>$('mdFlow')?.insertAdjacentHTML('afterbegin',freshnessHtml));
      const proposals=Array.isArray(proposalData.proposals)?proposalData.proposals:[];
      $('mdFlow').innerHTML=proposals.map(proposal=>{
        const matches=proposalMatches(catalog,proposal);
        const first=matches[0]?.row;
        const searchHref=`../owner-yarns/?query=${encodeURIComponent(proposal.primary_query||'')}`;
        const knitHref=first?`../knit-image/?source=catalog&id=${encodeURIComponent(first.catalog_id)}`:'../knit-image/';
        return`<article class="flow-card"><div class="flow-title"><div><div class="tag-row"><span class="tag">${esc(latest.observed_date)}／64ブランド</span><span class="tag pending">${esc(proposal.status)}</span><span class="tag pending">${esc(proposal.publication_status)}</span></div><h3>${esc(proposal.title)}</h3><p>${esc(proposal.scope_note)}</p></div><a href="../${esc(latest.summary_path)}" target="_blank" rel="noopener">観測サマリー</a></div><div class="flow-grid"><div class="flow-step"><span>1. 日次MD観測</span><strong>${esc(proposal.observed_signal)}</strong></div><div class="flow-step"><span>2. 市場変化・MD解釈</span><strong>${esc(proposal.market_change)}</strong></div><div class="flow-step"><span>3. 関連糸候補 ${matches.length.toLocaleString('ja-JP')}件</span><div class="candidate-list">${candidateHtml(matches)}</div></div><div class="flow-step"><span>4. 素材提案</span><strong>${esc(proposal.material_proposal)}</strong></div></div><div class="actions"><a class="btn" href="${searchHref}">糸検索で全候補を見る</a><a class="btn secondary" href="${knitHref}">候補から編み地イメージ</a></div></article>`;
      }).join('')||'<div class="empty">MD提案はまだありません。</div>';
    }catch(error){$('mdFlow').innerHTML=`<div class="empty">64ブランドMD導線を読み込めませんでした。${esc(error.message)}</div>`}
  }

  $('marketForm').addEventListener('submit',event=>{event.preventDefault();try{const row=observationFromForm(event.currentTarget);if(!row.observed_on||!row.market||!row.source_name)throw new Error('観測日、中国の市場・地域、情報源名を入力してください。');const state=loadState();state.observations.push(row);saveState(state);event.currentTarget.reset();$('observedOn').value=localDate();$('market').value='中国';setMessage(`${row.observation_id} をPENDING_HUMAN_REVIEWで追記しました。`);render()}catch(error){setMessage(`保存できませんでした。既存記録は変更していません: ${error.message||error}`,true)}});
  $('resetForm').addEventListener('click',()=>setTimeout(()=>{$('observedOn').value=localDate();$('market').value='中国';setMessage('')},0));
  $('recordSearch').addEventListener('input',render);
  $('exportJson').addEventListener('click',()=>{const state=loadState();if(!state.observations.length){setMessage('書き出す相場観測がありません。',true);return}const blob=new Blob([JSON.stringify({...state,exported_at:nowIso(),conversion_policy:'NO_AUTOMATIC_CONVERSION'},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`kc_china_market_intelligence_${localDate()}.json`;link.rel='noopener';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);setMessage(`${state.observations.length}件の監査JSONを書き出しました。`)});
  window.addEventListener('storage',event=>{if(event.key===STORAGE_KEY)render()});
  $('observedOn').value=localDate();render();loadMdFlow();
})();
