(()=>{
  'use strict';

  const DATA_URL='../data/market-trends/market-signals.json';
  const FEATURED_SIGNAL_ID='cellulosic-autumn-melange';
  const $=selector=>document.querySelector(selector);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));

  function injectStyles(){
    if(document.getElementById('kcMarketTrendStyles'))return;
    const style=document.createElement('style');
    style.id='kcMarketTrendStyles';
    style.textContent=`
      .market-trend-section{margin:18px 0 4px}
      .market-trend-boundary{display:flex;justify-content:space-between;gap:12px;align-items:center;margin:0 0 10px;padding:11px 13px;border:1px solid #d7d0ea;border-radius:13px;background:#faf8ff;color:#5e4e8c;font-size:9px}
      .market-trend-boundary strong{font-size:10px}
      .market-trend-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
      .market-trend-card{display:grid;gap:12px;min-width:0;padding:18px;border:1px solid #d6dfdb;border-radius:17px;background:#fff;box-shadow:0 8px 28px rgba(23,40,38,.06)}
      .market-trend-card.featured{border-color:#b9cfc6;background:linear-gradient(145deg,#fff,#f4faf7)}
      .market-trend-header{display:flex;justify-content:space-between;gap:14px;align-items:start}
      .market-trend-kicker{font-size:8px;font-weight:950;letter-spacing:.14em;color:#235c56}
      .market-trend-card h3{margin:3px 0 0;font-size:21px;line-height:1.16;letter-spacing:-.035em}
      .market-trend-en{margin-top:3px;color:#5d6d69;font-size:10px;font-weight:800}
      .market-trend-date{white-space:nowrap;color:#5d6d69;font-size:8px;font-weight:900}
      .market-trend-insight{margin:0;color:#31423f;font-size:11px}
      .market-trend-thesis{margin:0;padding:11px 12px;border-left:4px solid #2d655c;border-radius:0 11px 11px 0;background:#edf6f1;color:#244a42;font-size:12px;font-weight:900}
      .market-trend-meta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
      .market-trend-block{min-width:0;padding:10px;border-radius:11px;background:#eef3f1}
      .market-trend-block span{display:block;color:#5d6d69;font-size:8px;font-weight:950}
      .market-trend-block p{margin:4px 0 0;color:#172826;font-size:9px}
      .market-trend-tags{display:flex;flex-wrap:wrap;gap:5px}
      .market-trend-tags span{display:inline-flex;padding:4px 7px;border:1px solid #d2ded9;border-radius:999px;background:#f7faf8;color:#31594c;font-size:8px;font-weight:850}
      .market-trend-actions{display:flex;flex-wrap:wrap;gap:7px;align-items:center}
      .market-trend-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:36px;padding:7px 10px;border:1px solid #aabcb5;border-radius:9px;background:#fff;color:#163f3c;text-decoration:none;font-size:9px;font-weight:900}
      .market-trend-actions a.primary{border-color:#163f3c;background:#163f3c;color:#fff}
      .market-trend-sources{display:flex;flex-wrap:wrap;gap:5px}
      .market-trend-sources a{color:#235c56;font-size:8px;font-weight:850;overflow-wrap:anywhere}
      .market-trend-card details{border-top:1px solid #d6dfdb;padding-top:9px}
      .market-trend-card summary{cursor:pointer;color:#5d6d69;font-size:9px;font-weight:900}
      .market-trend-card ul{margin:7px 0 0;padding-left:18px;color:#465652;font-size:9px}
      .market-trend-empty{grid-column:1/-1;padding:24px 14px;border:1px dashed #aebdb7;border-radius:13px;background:#fff;color:#5d6d69;text-align:center;font-size:11px}
      @media(max-width:880px){.market-trend-grid{grid-template-columns:1fr}}
      @media(max-width:640px){.market-trend-section{margin-top:12px}.market-trend-boundary{align-items:flex-start;flex-direction:column}.market-trend-card{padding:14px}.market-trend-header{flex-direction:column}.market-trend-meta{grid-template-columns:1fr}.market-trend-actions a{width:100%}}
    `;
    document.head.appendChild(style);
  }

  function sourceRows(signal){
    return [signal.source,...(Array.isArray(signal.supporting_sources)?signal.supporting_sources:[])]
      .filter(source=>source&&source.url);
  }

  function listText(values,limit=6){
    return (Array.isArray(values)?values:[]).slice(0,limit).join('・')||'未登録';
  }

  function signalCard(signal){
    const keywords=(Array.isArray(signal.keywords)?signal.keywords:[]).slice(0,8)
      .map(value=>`<span>${esc(value)}</span>`).join('');
    const sources=sourceRows(signal).map((source,index)=>
      `<a href="${esc(source.url)}" target="_blank" rel="noopener">根拠${index+1}: ${esc(source.publisher||source.title||'出典')}</a>`
    ).join('');
    const watchPoints=(Array.isArray(signal.watch_points)?signal.watch_points:[])
      .map(value=>`<li>${esc(value)}</li>`).join('');
    const status=String(signal.status||'SIGNAL').replaceAll('_',' ');
    const featured=signal.id===FEATURED_SIGNAL_ID?' featured':'';
    const scopeNote=signal.scope_note?`<p class="market-trend-insight">${esc(signal.scope_note)}</p>`:'';

    return `<article class="market-trend-card${featured}">
      <div class="market-trend-header">
        <div>
          <div class="market-trend-kicker">MARKET SIGNAL / ${esc(status)}</div>
          <h3>${esc(signal.name_ja||signal.id)}</h3>
          <div class="market-trend-en">${esc(signal.name_en||'')}</div>
        </div>
        <div class="market-trend-date">観測 ${esc(signal.observed_at||'未設定')}</div>
      </div>
      <p class="market-trend-insight">${esc(signal.consumer_insight||'市場解釈を準備中です。')}</p>
      ${scopeNote}
      <blockquote class="market-trend-thesis">${esc(signal.proposal_thesis||'素材提案への接続を準備中です。')}</blockquote>
      <div class="market-trend-meta">
        <div class="market-trend-block"><span>推奨糸・構造</span><p>${esc(listText(signal.recommended_yarn_types,6))}</p></div>
        <div class="market-trend-block"><span>推奨編地・用途</span><p>${esc(listText(signal.recommended_knits,6))}</p></div>
      </div>
      <div class="market-trend-tags">${keywords}</div>
      <div class="market-trend-actions">
        <a class="primary" href="../owner-yarns/?trend=${encodeURIComponent(signal.id)}">関連糸候補を見る</a>
        <div class="market-trend-sources">${sources}</div>
      </div>
      ${watchPoints?`<details><summary>開発・品質上の注意点</summary><ul>${watchPoints}</ul></details>`:''}
    </article>`;
  }

  function mount(){
    if(document.getElementById('marketSignalSection'))return document.getElementById('marketSignalList');
    const stats=$('section.stats');
    if(!stats)return null;
    const section=document.createElement('section');
    section.className='market-trend-section';
    section.id='marketSignalSection';
    section.setAttribute('aria-label','素材トレンド');
    section.innerHTML=`
      <div class="section-head">
        <div>
          <h2>素材トレンド / Market Signals</h2>
          <p>ブランド商品、気象、展示会・業界情報から、素材開発につながる変化を独立して追跡します。</p>
        </div>
        <div class="tag-row"><span class="tag">素材トレンド</span><span class="tag pending">MD解釈</span><span class="tag pending">数量未集計</span></div>
      </div>
      <div class="market-trend-boundary">
        <strong>事実と解釈を分離</strong>
        <span>商品・外部資料は根拠リンクを保持し、トレンド判断は素材開発上の仮説として表示します。原料相場の確認済み数値とは混在させません。</span>
      </div>
      <div class="market-trend-grid" id="marketSignalList"><div class="market-trend-empty">素材トレンドを読み込んでいます。</div></div>
    `;
    stats.insertAdjacentElement('beforebegin',section);
    return document.getElementById('marketSignalList');
  }

  async function loadSignals(){
    injectStyles();
    const list=mount();
    if(!list)return;
    try{
      const response=await fetch(DATA_URL,{cache:'no-store'});
      if(!response.ok)throw new Error(`HTTP ${response.status}`);
      const data=await response.json();
      const signals=(Array.isArray(data.signals)?data.signals:[])
        .filter(signal=>signal&&signal.status==='ACTIVE_SIGNAL')
        .sort((a,b)=>{
          if(a.id===FEATURED_SIGNAL_ID)return -1;
          if(b.id===FEATURED_SIGNAL_ID)return 1;
          return String(b.observed_at||'').localeCompare(String(a.observed_at||''));
        });
      list.innerHTML=signals.length?signals.map(signalCard).join(''):'<div class="market-trend-empty">表示できる素材トレンドはまだありません。</div>';
    }catch(error){
      list.innerHTML=`<div class="market-trend-empty">素材トレンドを読み込めませんでした。${esc(error.message||error)}</div>`;
    }
  }

  loadSignals();
})();