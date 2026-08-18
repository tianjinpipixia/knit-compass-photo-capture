(()=>{
  'use strict';

  const TERMS=[
    {
      id:'KC-SIRO-001',
      display:'Siro／赛络纺',
      japanese:'サイロ紡績／サイロ糸',
      chinese:['赛络纺','赛络纺纱','赛络纱'],
      english:['Siro','Siro spinning','Sirospun'],
      structure:'短繊維束 × 短繊維束',
      description:'2本の短繊維束（ロービング）を別々にドラフトし、合流後に同時加撚するリング系紡績。短繊維束×短繊維束の構造で、通常の単糸より毛羽低減・均斉性向上・双糸調の外観を狙う。',
      rule:'最終紡績方式＝Ring系／糸構造＝Siro。Sirofil、Core-spunとは別分類。',
      checks:['短繊維束の本数','ロービング間隔','撚数・撚方向','番手','前紡工程','編立ゲージ'],
      keywords:['サイロ','サイロ紡績','サイロ糸','赛络纺','赛络纺纱','赛络纱','Siro','Siro spinning','Sirospun']
    },
    {
      id:'KC-SIRO-002',
      display:'Sirofil／赛络菲尔纺',
      japanese:'サイロフィル紡績／サイロフィル糸',
      chinese:['赛络菲尔纺','赛络菲尔纱'],
      english:['Sirofil','Sirofil spinning','Sirofil yarn'],
      structure:'短繊維束 × 連続フィラメント',
      description:'短繊維束（ロービング）と連続フィラメントを別経路から供給し、合流後に同時加撚する複合紡績。短繊維束×フィラメントの構造で、フィラメントは必ずしも中心芯に固定されないためCore-spunとは別分類とする。',
      rule:'最終紡績方式＝Ring系／糸構造＝Sirofil。Core-spunへ自動変換しない。',
      checks:['フィラメント素材','D数・F数','フィラメント供給位置','ロービングとの間隔','フィラメント張力','撚数・撚方向','番手','編立ゲージ'],
      keywords:['サイロフィル','サイロフィル紡績','サイロフィル糸','赛络菲尔纺','赛络菲尔纱','Sirofil','Sirofil spinning','Sirofil yarn']
    },
    {
      id:'KC-SIRO-003',
      display:'Core-spun／包芯纱',
      japanese:'コアスパンヤーン／芯鞘型紡績糸',
      chinese:['包芯纱','包芯纺','包芯纱线'],
      english:['core-spun','core spun yarn','core spinning'],
      structure:'中心芯 ＋ 外側短繊維',
      description:'フィラメントや弾性糸などの芯材を中心に配置し、その周囲を短繊維で被覆して紡績する構造。中心芯＋外側短繊維の構造で、Sirofilとはフィラメントの配置思想が異なる。',
      rule:'糸構造＝Core-spun。最終紡績方式はRing／Compact／その他を別途確認し、名称だけから決めない。',
      checks:['芯材の種類','芯材番手・D数','芯材位置','被覆短繊維','カバレッジ','撚数・撚方向','番手','編立ゲージ'],
      keywords:['コアスパン','コアスパンヤーン','芯鞘糸','芯糸紡績','包芯纱','包芯纺','包芯纱线','core-spun','core spun yarn','core spinning']
    }
  ];

  const normalize=value=>String(value||'').toLowerCase().normalize('NFKC').replace(/[／/・,、()（）\-]+/g,' ').replace(/\s+/g,' ').trim();
  const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
  const tags=(items,klass='')=>(items||[]).map(value=>`<span class="tag ${klass}">${esc(value)}</span>`).join('');

  function termText(term){return normalize([term.display,term.japanese,...term.chinese,...term.english,term.structure,term.description,term.rule,...term.checks,...term.keywords].join(' '));}

  function card(term,doc){
    const article=doc.createElement('article');
    article.className='card kc-siro-term-card';
    article.dataset.kcSiroTerm=term.id;
    article.innerHTML=`
      <div class="card-head"><div><div class="market">${esc(term.display)}</div><div class="jp">${esc(term.japanese)}</div></div><span class="priority">構造標準</span></div>
      <div><div style="font-size:9px;color:var(--muted);font-weight:900;margin-bottom:5px">構造</div><div class="tags"><span class="tag type">${esc(term.structure)}</span></div></div>
      <div class="row"><strong>中国語表記</strong><div class="tags">${tags(term.chinese)}</div></div>
      <div class="row"><strong>英語検索語</strong><div class="tags">${tags(term.english)}</div></div>
      <div class="row"><strong>日本語検索語</strong><div class="tags">${tags(term.keywords.filter(value=>/[ぁ-んァ-ヶ一-龠]/.test(value)))}</div></div>
      <div class="warning"><strong>説明：</strong>${esc(term.description)}</div>
      <div class="match"><strong>KC分類ルール：</strong>${esc(term.rule)}</div>
      <div class="row"><strong>Supplier確認ポイント</strong><div>${esc(term.checks.join(' ／ '))}</div></div>
      <div class="row"><strong>検索キーワード</strong><div class="tags">${tags(term.keywords)}</div></div>
      <div class="actions"><a class="mini" href="./siro-sirofil-core-spun.html" target="_top">技術解説を開く</a></div>`;
    return article;
  }

  function install(){
    const frame=document.getElementById('contentFrame');
    if(!(frame instanceof HTMLIFrameElement))return;

    const apply=()=>{
      let doc;
      try{doc=frame.contentDocument;}catch{return;}
      if(!doc||!String(frame.getAttribute('src')||'').includes('yarn-glossary.html'))return;
      const list=doc.getElementById('list');
      const query=doc.getElementById('query');
      const category=doc.getElementById('category');
      if(!list||!query||!category)return;

      if(![...category.options].some(option=>option.value==='糸構造・複合紡績')){
        const option=doc.createElement('option'); option.value='糸構造・複合紡績'; option.textContent='糸構造・複合紡績'; category.appendChild(option);
      }

      list.querySelectorAll('.kc-siro-term-card').forEach(node=>node.remove());
      const q=normalize(query.value);
      const cat=category.value;
      const visible=TERMS.filter(term=>(!q||termText(term).includes(q))&&(!cat||cat==='糸構造・複合紡績'));
      visible.forEach(term=>list.appendChild(card(term,doc)));

      const total=doc.getElementById('totalCount');
      const shown=doc.getElementById('visibleCount');
      if(total&&!total.dataset.kcSiroBase){total.dataset.kcSiroBase=total.textContent||'0';}
      if(shown&&!shown.dataset.kcSiroBase){shown.dataset.kcSiroBase=shown.textContent||'0';}
      const parse=value=>Number(String(value||'0').replace(/\D/g,''))||0;
      if(total)total.textContent=String(parse(total.dataset.kcSiroBase)+TERMS.length);
      if(shown)shown.textContent=String(parse(shown.dataset.kcSiroBase)+visible.length);
    };

    frame.addEventListener('load',()=>{
      apply();
      let doc; try{doc=frame.contentDocument;}catch{return;}
      if(!doc)return;
      const rerender=()=>setTimeout(apply,0);
      doc.getElementById('query')?.addEventListener('input',rerender);
      doc.getElementById('category')?.addEventListener('change',rerender);
      doc.getElementById('clear')?.addEventListener('click',rerender);
      const observer=new MutationObserver(()=>{if(!doc.querySelector('.kc-siro-term-card'))setTimeout(apply,0);});
      const list=doc.getElementById('list'); if(list)observer.observe(list,{childList:true});
    });
  }

  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});else install();
})();
