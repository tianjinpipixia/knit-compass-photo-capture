(()=>{
  'use strict';

  const DATA_URL='../data/market-trends/market-signals.json';
  const FALLBACK_SIGNALS=[{
    id:'analog-revival',
    name_ja:'アナログ回帰',
    name_en:'Analog Revival',
    consumer_insight:'常時接続・効率化への反動から、触感・クラフト・ヴィンテージ・所有感が再評価される。',
    keywords:['Y2K','Craft','Vintage','Texture','Imperfection'],
    recommended_yarn_types:['仿安哥拉','仿兔毛','仿貂绒','モヘア調','ネップ','スラブ','ブークレ','杢','麻見え'],
    source:{publisher:'VOGUE JAPAN',url:'https://www.vogue.co.jp/article/genz-analog-revival'},
    match_rules:[
      {label:'毛羽・ノスタルジー',terms:['仿安哥拉','安哥拉','兔绒','兔毛','仿兔','貂绒','仿貂','马海毛','mohair','モヘア','羽毛纱','feather','フェザー']},
      {label:'クラフト凹凸',terms:['圈圈','boucle','ブークレ','竹节','slub','スラブ','结子','nep','ネップ','雪尼尔','chenille','粗纺','粗针']},
      {label:'ヴィンテージ杢',terms:['花灰','麻灰','彩点','段染','雪花','tweed','ツイード','粗花呢','彩纱']},
      {label:'天然・麻見え',terms:['亚麻','苎麻','棉麻','仿麻','linen','ramie','リネン','ラミー']}
    ]
  }];

  const normalize=value=>String(value??'').toLowerCase().normalize('NFKC');
  const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));

  async function loadSignals(){
    try{
      const response=await fetch(DATA_URL,{cache:'no-store'});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const data=await response.json();
      if(!Array.isArray(data.signals)||!data.signals.length)throw new Error('signals missing');
      return data.signals;
    }catch(error){
      console.warn('Market Signals fallback:',error);
      return FALLBACK_SIGNALS;
    }
  }

  function injectStyles(){
    if(document.getElementById('kcMarketSignalStyles'))return;
    const style=document.createElement('style');
    style.id='kcMarketSignalStyles';
    style.textContent=`
      .kc-market-shell{grid-template-rows:auto auto minmax(0,1fr)!important}
      .kc-market-strip{background:linear-gradient(90deg,#f5faf7,#fff9ef);border-bottom:1px solid #d6dfdb;padding:8px 10px;color:#172826}
      .kc-market-strip-inner{width:min(1180px,100%);margin:auto;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:12px;align-items:center}
      .kc-market-kicker{font-size:8px;font-weight:950;letter-spacing:.14em;color:#235c56;text-transform:uppercase}
      .kc-market-title{font-size:14px;font-weight:950;letter-spacing:-.02em;margin-top:1px}
      .kc-market-desc{font-size:9px;color:#5d6d69;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      .kc-market-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:5px}.kc-market-tags span{display:inline-flex;border-radius:999px;padding:2px 6px;background:#edf4ef;color:#31594c;border:1px solid #cfddd4;font-size:7px;font-weight:900}
      .kc-market-actions{display:flex;gap:6px;align-items:center}.kc-market-link{display:inline-flex;align-items:center;justify-content:center;min-height:34px;border:1px solid #aabcb5;border-radius:9px;background:#fff;color:#163f3c;text-decoration:none;padding:6px 10px;font-size:9px;font-weight:900;white-space:nowrap}.kc-market-link.primary{background:#163f3c;color:#fff;border-color:#163f3c}
      .kc-trend-prompt{display:flex;justify-content:space-between;gap:12px;align-items:center;border:1px solid #d8d0e9;background:#faf8ff;border-radius:13px;padding:11px 13px;margin-top:12px}.kc-trend-prompt strong{display:block;font-size:12px}.kc-trend-prompt span{display:block;color:#5d6d69;font-size:9px;margin-top:2px}.kc-trend-toolbar{grid-template-columns:minmax(240px,1fr) 190px 150px 180px auto!important}.kc-trend-tag{background:#eeeafb!important;color:#5e4e8c!important}.kc-trend-reason{font-size:9px;color:#5d6d69;padding:8px 9px;border-radius:9px;background:#faf8ff;border:1px solid #ebe6f5}.kc-trend-count{font-weight:950;color:#5e4e8c}
      @media(max-width:900px){.kc-trend-toolbar{grid-template-columns:1fr 1fr!important}.kc-market-strip-inner{grid-template-columns:1fr auto}}
      @media(max-width:760px){.kc-market-shell{grid-template-rows:auto auto minmax(0,1fr)!important}.kc-market-strip{padding:7px}.kc-market-strip-inner{grid-template-columns:1fr;gap:6px}.kc-market-desc{white-space:normal;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}.kc-market-actions{justify-content:flex-start;overflow:auto}.kc-market-link{min-height:32px}}
      @media(max-width:620px){.kc-trend-toolbar{grid-template-columns:1fr!important}.kc-trend-prompt{align-items:flex-start;flex-direction:column}.kc-trend-prompt .btn{width:100%}}
    `;
    document.head.appendChild(style);
  }

  function matchSignal(row,signal){
    const hay=normalize([row?.name,row?.count_display,row?.composition_raw,row?.listed_supplier,row?.source_id].filter(Boolean).join(' '));
    const reasons=[];
    for(const rule of signal.match_rules||[]){
      if((rule.terms||[]).some(term=>hay.includes(normalize(term))))reasons.push(rule.label);
    }
    return {id:signal.id,label:`${signal.name_en} / ${signal.name_ja}`,reasons:[...new Set(reasons)]};
  }

  function initTop(signals){
    const frame=document.getElementById('contentFrame');
    const shell=frame?.closest('.shell');
    const header=shell?.querySelector('.switcher');
    if(!frame||!shell||!header||document.getElementById('kcMarketSignal'))return;
    const signal=signals.find(item=>item.id==='analog-revival')||signals[0];
    if(!signal)return;
    const section=document.createElement('section');
    section.className='kc-market-strip';
    section.id='kcMarketSignal';
    section.setAttribute('aria-label','市場トレンド');
    const tags=(signal.keywords||[]).slice(0,5).map(tag=>`<span>${escapeHtml(tag)}</span>`).join('');
    section.innerHTML=`<div class="kc-market-strip-inner"><div><div class="kc-market-kicker">MARKET SIGNALS / 市場トレンド</div><div class="kc-market-title">${escapeHtml(signal.name_en)} / ${escapeHtml(signal.name_ja)}</div><div class="kc-market-desc">デジタル疲れ・効率化への反動。毛羽・凹凸・杢・麻見えなど「触りたい・持ちたい」質感を素材提案へ。</div><div class="kc-market-tags">${tags}</div></div><div class="kc-market-actions"><a class="kc-market-link primary" href="../owner-yarns/?trend=${encodeURIComponent(signal.id)}" target="_top">関連素材を見る</a><a class="kc-market-link" href="${escapeHtml(signal.source?.url||'https://www.vogue.co.jp/article/genz-analog-revival')}" target="_blank" rel="noopener">VOGUE記事</a></div></div>`;
    header.insertAdjacentElement('afterend',section);
    const setVisibility=hidden=>{section.hidden=hidden;shell.classList.toggle('kc-market-shell',!hidden)};
    const syncVisibility=()=>setVisibility(location.hash==='#cn-yarn-glossary');
    document.getElementById('tabGlossary')?.addEventListener('click',()=>setVisibility(true));
    document.getElementById('tabV04')?.addEventListener('click',()=>setVisibility(false));
    window.addEventListener('popstate',syncVisibility);
    syncVisibility();
  }

  function initOwner(signals){
    const grid=document.getElementById('catalogGrid');
    const toolbar=grid?.parentElement?.querySelector('.toolbar');
    if(!(grid instanceof Element)||!(toolbar instanceof Element)||document.getElementById('kcTrendFilter'))return;
    const signal=signals.find(item=>item.id==='analog-revival')||signals[0];
    if(!signal)return;

    const notice=toolbar.previousElementSibling;
    const prompt=document.createElement('div');
    prompt.className='kc-trend-prompt';
    prompt.innerHTML=`<div><strong>${escapeHtml(signal.name_en)} / ${escapeHtml(signal.name_ja)}</strong><span>毛羽・凹凸・杢・麻見えを2,000件から横断抽出。元カタログの事実データは変更せず、トレンド解釈だけを重ねます。</span></div><button class="btn secondary" id="kcAnalogTrendButton" type="button">関連素材を見る <span class="kc-trend-count" id="kcTrendMatchCount">—</span></button>`;
    if(notice?.classList.contains('notice'))notice.insertAdjacentElement('afterend',prompt);else toolbar.insertAdjacentElement('beforebegin',prompt);

    toolbar.classList.add('kc-trend-toolbar');
    const label=document.createElement('label');
    label.className='field';
    label.innerHTML='<span>市場トレンド</span><select id="kcTrendFilter"><option value="all">すべて</option></select>';
    toolbar.insertBefore(label,toolbar.lastElementChild);
    const select=document.getElementById('kcTrendFilter');
    for(const item of signals){
      const option=document.createElement('option');
      option.value=item.id;
      option.textContent=`${item.name_en} / ${item.name_ja}`;
      select.appendChild(option);
    }

    function enrichRows(){
      if(typeof catalog==='undefined'||!Array.isArray(catalog))return;
      for(const row of catalog){
        row.market_trend_tags=signals.map(item=>matchSignal(row,item)).filter(match=>match.reasons.length);
      }
      const matches=catalog.filter(row=>(row.market_trend_tags||[]).some(item=>item.id===signal.id)).length;
      const count=document.getElementById('kcTrendMatchCount');
      if(count)count.textContent=`${matches.toLocaleString('ja-JP')}件`;
    }

    function decorateCards(){
      if(typeof filtered==='undefined'||!Array.isArray(filtered)||typeof visible==='undefined')return;
      enrichRows();
      const rows=filtered.slice(0,visible);
      [...grid.querySelectorAll('.yarn-card')].forEach((card,index)=>{
        card.querySelector('.kc-trend-decoration')?.remove();
        const row=rows[index];
        const matches=row?.market_trend_tags||[];
        if(!matches.length)return;
        const block=document.createElement('div');
        block.className='kc-trend-decoration';
        const tagRow=document.createElement('div');
        tagRow.className='tags';
        for(const match of matches){
          const tag=document.createElement('span');
          tag.className='tag kc-trend-tag';
          tag.textContent=match.label;
          tagRow.appendChild(tag);
        }
        const reason=document.createElement('div');
        reason.className='kc-trend-reason';
        reason.textContent=`提案理由：${matches.map(item=>item.reasons.join('・')).join(' / ')}`;
        block.append(tagRow,reason);
        const facts=card.querySelector('.facts');
        if(facts)facts.insertAdjacentElement('afterend',block);else card.appendChild(block);
      });
    }

    function applySelectedTrend(){
      enrichRows();
      if(select.value==='all'){decorateCards();return}
      if(typeof filtered==='undefined'||!Array.isArray(filtered)||typeof renderCatalog!=='function')return;
      filtered=filtered.filter(row=>(row.market_trend_tags||[]).some(item=>item.id===select.value));
      if(typeof visible!=='undefined')visible=48;
      renderCatalog();
      decorateCards();
    }

    function applyBaseThenTrend(){
      if(typeof applyFilters==='function')applyFilters();
      applySelectedTrend();
    }

    select.addEventListener('change',applyBaseThenTrend);
    document.getElementById('kcAnalogTrendButton')?.addEventListener('click',()=>{select.value=signal.id;applyBaseThenTrend();toolbar.scrollIntoView({behavior:'smooth',block:'start'})});
    document.getElementById('applySearch')?.addEventListener('click',()=>queueMicrotask(applySelectedTrend));
    document.getElementById('query')?.addEventListener('keydown',event=>{if(event.key==='Enter')queueMicrotask(applySelectedTrend)});
    document.getElementById('resetSearch')?.addEventListener('click',()=>{select.value='all';queueMicrotask(decorateCards)});
    document.getElementById('loadMore')?.addEventListener('click',()=>queueMicrotask(decorateCards));

    const requested=new URLSearchParams(location.search).get('trend');
    let initialApplied=false;
    const tryInitial=()=>{
      if(initialApplied||typeof catalog==='undefined'||!Array.isArray(catalog)||!catalog.length)return false;
      initialApplied=true;
      enrichRows();
      if(requested&&signals.some(item=>item.id===requested))select.value=requested;
      if(select.value!=='all')applyBaseThenTrend();else decorateCards();
      return true;
    };
    if(!tryInitial()){
      let attempts=0;
      const readyTimer=setInterval(()=>{
        attempts+=1;
        if(!grid.isConnected||tryInitial()||attempts>=100)clearInterval(readyTimer);
      },100);
    }
  }

  async function boot(){
    injectStyles();
    const signals=await loadSignals();
    initTop(signals);
    initOwner(signals);
  }

  boot();
})();
