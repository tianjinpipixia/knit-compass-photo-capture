(()=>{
  'use strict';

  const V04_KEY='kc_independent_practical_v0_4';
  const CATALOG_URLS=['../data/yarn-catalog/mz100-catalog-3000.json','../data/yarn-catalog/mz100-catalog-2000.json'];
  const RESULT_LIMIT=80;
  const STRUCTURE_LABELS={
    jersey:'天竺','full-needle':'総針',rib:'リブ',interlock:'スムース',milano:'ミラノリブ',
    garter:'ガーター',pique:'鹿の子','half-cardigan':'片畦','full-cardigan':'両畦',
    jacquard:'ジャカード',cable:'ケーブル',mesh:'透かし・メッシュ'
  };
  const $=id=>document.getElementById(id);
  const esc=value=>String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[char]));
  const normalize=value=>String(value||'').toLowerCase().replace(/[／/・,、()（）\-]+/g,' ').replace(/\s+/g,' ').trim();
  const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
  let catalogYarns=[];
  let masterYarns=[];
  let selectedYarn=null;
  let renderedYarns=[];
  let generationVariant=0;

  function loadMasterYarns(){
    try{
      const state=JSON.parse(localStorage.getItem(V04_KEY)||'{}');
      const rows=Array.isArray(state.yarns)?state.yarns:[];
      return rows.map(row=>({
        id:String(row.id||`MASTER-${row.code||row.name||''}`),source:'master',name:row.name||'名称未設定',
        supplier:row.supplier||'',code:row.code||'',count:row.displayCount||row.countDisplay||row.countValue||'',
        composition:row.composition||row.compositionRaw||'',structure:row.structure||row.yarnStructure||'',
        gauge:row.gauge||'',knittingEnds:row.knittingEnds||'',status:row.status||'DRAFT',
        sourceUrl:row.sourceUrl||'',raw:row
      }));
    }catch{return[]}
  }

  async function loadCatalogYarns(){
    let data,lastError;
    for(const url of CATALOG_URLS){try{const response=await fetch(url,{cache:'no-store'});if(!response.ok)throw new Error(`糸カタログ HTTP ${response.status}`);data=await response.json();if(Array.isArray(data.records))break}catch(error){lastError=error}}
    if(!data||!Array.isArray(data.records))throw lastError||new Error('糸カタログを読み込めませんでした。');
    const rows=Array.isArray(data.records)?data.records:[];
    return rows.map(row=>({
      id:String(row.catalog_id||`CAT-${row.source_id||row.name||''}`),source:'catalog',name:row.name||'名称未設定',
      supplier:row.listed_supplier||'',code:row.source_id||'',count:row.count_display||'',
      composition:row.composition_raw||'',structure:'',gauge:'',knittingEnds:'',
      status:row.master_status||'NOT_PROMOTED',sourceUrl:row.source_url||'',raw:row
    }));
  }

  function yarnSearchText(yarn){
    return normalize([yarn.id,yarn.name,yarn.supplier,yarn.code,yarn.count,yarn.composition,yarn.structure,yarn.gauge,yarn.status].join(' '));
  }

  function sourceLabel(yarn){return yarn.source==='master'?'V04マスター':`${catalogYarns.length.toLocaleString('ja-JP')}件カタログ`}

  function renderYarnResults(){
    const source=$('sourceFilter').value;
    const terms=normalize($('yarnQuery').value).split(' ').filter(Boolean);
    const all=[...masterYarns,...catalogYarns];
    renderedYarns=all.filter(yarn=>(source==='all'||yarn.source===source)&&terms.every(term=>yarnSearchText(yarn).includes(term))).slice(0,RESULT_LIMIT);
    const total=all.filter(yarn=>(source==='all'||yarn.source===source)&&terms.every(term=>yarnSearchText(yarn).includes(term))).length;
    $('sourceCounts').textContent=`V04 ${masterYarns.length}件＋カタログ ${catalogYarns.length.toLocaleString('ja-JP')}件／該当 ${total.toLocaleString('ja-JP')}件`;
    $('yarnResults').innerHTML=renderedYarns.length?renderedYarns.map(yarn=>`
      <button class="yarn-option ${selectedYarn?.id===yarn.id&&selectedYarn?.source===yarn.source?'selected':''}" type="button" data-yarn-source="${esc(yarn.source)}" data-yarn-id="${esc(yarn.id)}">
        <span class="option-head"><strong>${esc(yarn.name)}</strong><span class="source-tag ${yarn.source}">${esc(sourceLabel(yarn))}</span></span>
        <p>${esc([yarn.supplier,yarn.count,yarn.composition].filter(Boolean).join(' ／ ')||'番手・混率 要確認')}</p>
      </button>`).join(''):`<div class="empty">条件に一致する糸がありません。</div>`;
    document.querySelectorAll('[data-yarn-id]').forEach(button=>button.addEventListener('click',()=>{
      const yarn=[...masterYarns,...catalogYarns].find(row=>row.source===button.dataset.yarnSource&&row.id===button.dataset.yarnId);
      if(yarn)selectYarn(yarn,true);
    }));
  }

  function selectedFacts(yarn){
    const facts=[['番手',yarn.count||'要確認'],['混率',yarn.composition||'要確認'],['糸構造',yarn.structure||'要確認'],['対応ゲージ',yarn.gauge||'要確認']];
    return facts.map(([label,value])=>`<div><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('');
  }

  function renderSelectedYarn(){
    if(!selectedYarn){$('selectedYarn').className='selected-yarn empty';$('selectedYarn').textContent='左の一覧から糸を選択してください。';$('generate').disabled=true;return}
    const catalog=selectedYarn.source==='catalog';
    $('selectedYarn').className='selected-yarn';
    $('selectedYarn').innerHTML=`
      <div class="selected-head"><div><h3>${esc(selectedYarn.name)}</h3><p>${esc([selectedYarn.supplier,selectedYarn.code].filter(Boolean).join(' ／ ')||sourceLabel(selectedYarn))}</p></div><span class="source-tag ${selectedYarn.source}">${esc(sourceLabel(selectedYarn))}</span></div>
      <div class="selected-facts">${selectedFacts(selectedYarn)}</div>
      <div class="source-boundary">${catalog?'CATALOG_INDEXED / LISTING_PAGE_ONLY / NOT_PROMOTED：仕様確定前の検索候補です。':`${esc(selectedYarn.status)}：端末内V04糸マスターを読み取り専用で参照しています。`}</div>`;
    $('generate').disabled=false;
  }

  function structureValue(text){
    const value=normalize(text);
    if(!value)return'jersey';
    if(/総針|full needle/.test(value))return'full-needle';
    if(/ミラノ|milano/.test(value))return'milano';
    if(/スムース|interlock/.test(value))return'interlock';
    if(/片畦|half cardigan/.test(value))return'half-cardigan';
    if(/両畦|full cardigan/.test(value))return'full-cardigan';
    if(/鹿の子|pique/.test(value))return'pique';
    if(/ガーター|garter/.test(value))return'garter';
    if(/ジャカード|jacquard/.test(value))return'jacquard';
    if(/ケーブル|cable/.test(value))return'cable';
    if(/透かし|メッシュ|mesh|lace/.test(value))return'mesh';
    if(/リブ|rib/.test(value))return'rib';
    return'jersey';
  }

  function applyYarnDefaults(){
    if(!selectedYarn)return;
    const gaugeMatch=String(selectedYarn.gauge||'').match(/(3|5|7|9|12|14|16|18)\s*G?/i);
    $('gauge').value=gaugeMatch?gaugeMatch[1]:'12';
    $('knitStructure').value=structureValue(selectedYarn.structure);
    const ends=Number(selectedYarn.knittingEnds);
    $('knittingEnds').value=Number.isInteger(ends)&&ends>=1&&ends<=6?String(ends):'1';
  }

  function selectYarn(yarn,updateUrl){
    selectedYarn=yarn;
    applyYarnDefaults();
    renderSelectedYarn();
    renderYarnResults();
    if(updateUrl){
      const url=new URL(location.href);url.searchParams.set('source',yarn.source);url.searchParams.set('id',yarn.id);history.replaceState(null,'',url);
    }
    $('generationStatus').textContent='ゲージ・編組織・本取りを確認し、「生成」を押してください。';
  }

  function hashString(value){let hash=2166136261;for(const char of String(value)){hash^=char.charCodeAt(0);hash=Math.imul(hash,16777619)}return hash>>>0}
  function randomFactory(seed){let value=seed>>>0;return()=>{value+=0x6D2B79F5;let t=value;t=Math.imul(t^t>>>15,t|1);t^=t+Math.imul(t^t>>>7,t|61);return((t^t>>>14)>>>0)/4294967296}}
  function hexToRgb(hex){const match=String(hex).match(/^#([0-9a-f]{6})$/i);if(!match)return{r:155,g:118,b:94};const n=parseInt(match[1],16);return{r:n>>16,g:n>>8&255,b:n&255}}
  function rgb(color,alpha=1){return`rgba(${Math.round(color.r)},${Math.round(color.g)},${Math.round(color.b)},${alpha})`}
  function mix(a,b,amount){return{r:a.r+(b.r-a.r)*amount,g:a.g+(b.g-a.g)*amount,b:a.b+(b.b-a.b)*amount}}
  function lighten(color,amount){return mix(color,{r:255,g:255,b:255},amount)}
  function darken(color,amount){return mix(color,{r:0,g:0,b:0},amount)}

  function drawLoop(ctx,x,y,width,height,color,lineWidth,flip=false){
    const path=()=>{ctx.beginPath();ctx.moveTo(x-width*.39,y-height*.38);ctx.bezierCurveTo(x-width*.2,y-height*.04,x-width*.1,y+height*.36,x,y+height*.42);ctx.bezierCurveTo(x+width*.1,y+height*.36,x+width*.2,y-height*.04,x+width*.39,y-height*.38)};
    ctx.save();ctx.translate(0,flip?height*.08:0);
    path();ctx.strokeStyle=rgb(darken(color,.43),.72);ctx.lineWidth=lineWidth*1.75;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke();
    path();ctx.strokeStyle=rgb(color,.96);ctx.lineWidth=lineWidth;ctx.stroke();
    path();ctx.strokeStyle=rgb(lighten(color,.55),.36);ctx.lineWidth=Math.max(1,lineWidth*.22);ctx.stroke();ctx.restore();
  }

  function drawLoopGrid(ctx,options){
    const {width,height,columns,rows,color,lineWidth,random,offset=0,colorAt}=options;
    const cellW=width/(columns-1),cellH=height/(rows-1);
    for(let row=0;row<rows;row++)for(let column=-1;column<=columns;column++){
      const stagger=(row%2)*cellW*.5;
      const x=column*cellW+stagger+cellW*.15+(random()-.5)*cellW*.055;
      const y=row*cellH+cellH*.42+(random()-.5)*cellH*.05+offset;
      drawLoop(ctx,x,y,cellW*.95,cellH*.95,colorAt?colorAt(row,column,color):color,lineWidth,row%2===1);
    }
    return{cellW,cellH};
  }

  function drawHorizontalRidges(ctx,width,height,color,spacing,lineWidth,random){
    for(let y=spacing*.45;y<height;y+=spacing){
      ctx.beginPath();ctx.moveTo(-20,y);for(let x=0;x<=width+20;x+=18)ctx.quadraticCurveTo(x+9,y+(random()-.5)*4,x+18,y);ctx.strokeStyle=rgb(darken(color,.38),.55);ctx.lineWidth=lineWidth*1.7;ctx.stroke();
      ctx.beginPath();ctx.moveTo(-20,y-2);ctx.lineTo(width+20,y-2);ctx.strokeStyle=rgb(lighten(color,.5),.28);ctx.lineWidth=Math.max(1,lineWidth*.35);ctx.stroke();
    }
  }

  function materialFeatures(yarn){
    const text=normalize([yarn.name,yarn.composition,yarn.structure].join(' '));
    return{
      fuzz:/wool|羊毛|cashmere|カシミヤ|羊绒|mohair|马海|alpaca|羊驼|fox|狐狸|貂|兔|angora/.test(text)?.9:/acrylic|アクリル|腈|晴纶/.test(text)?.45:.16,
      sheen:/silk|シルク|桑蚕丝|viscose|レーヨン|粘胶|rayon|nylon|ナイロン|锦纶|polyester|ポリエステル|涤纶|filament|フィラメント/.test(text)?.68:.18,
      irregular:/linen|麻|亚麻|hemp|ramie|high twist|強撚|高捻/.test(text)?.8:.2,
      fancy:/fancy|ファンシー|圈圈|珠片|羽毛|フェザー|feather|boucle|ブークレ|毛足/.test(text)?.9:.08
    };
  }

  function drawPattern(ctx,width,height,structure,gauge,ends,color,random){
    const columns=clamp(Math.round(18+gauge*2.25),22,62);
    const rows=clamp(Math.round(columns*.66),16,43);
    const cellW=width/(columns-1),cellH=height/(rows-1);
    const lineWidth=clamp(cellW*(.11+ends*.025),2.2,10.5);
    if(structure==='mesh'){
      const meshColumns=Math.max(12,Math.round(columns*.58)),meshRows=Math.max(10,Math.round(rows*.7));
      const mw=width/meshColumns,mh=height/meshRows;
      for(let row=-1;row<=meshRows;row++)for(let column=-1;column<=meshColumns;column++){
        const x=column*mw+(row%2)*mw*.5,y=row*mh;
        ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+mw*.5,y+mh*.5);ctx.lineTo(x,y+mh);ctx.lineTo(x-mw*.5,y+mh*.5);ctx.closePath();ctx.strokeStyle=rgb(darken(color,.32),.78);ctx.lineWidth=lineWidth*1.45;ctx.stroke();
        ctx.beginPath();ctx.moveTo(x,y+1);ctx.lineTo(x+mw*.5,y+mh*.5);ctx.strokeStyle=rgb(lighten(color,.55),.35);ctx.lineWidth=Math.max(1,lineWidth*.3);ctx.stroke();
      }
      return;
    }
    if(structure==='garter'){
      drawLoopGrid(ctx,{width,height,columns:Math.round(columns*.78),rows,color,lineWidth:lineWidth*.9,random});
      drawHorizontalRidges(ctx,width,height,color,cellH*.95,lineWidth,random);return;
    }
    if(structure==='rib'||structure==='full-needle'||structure==='half-cardigan'||structure==='full-cardigan'){
      const ribEvery=structure==='full-needle'?1:2;
      for(let column=0;column<columns;column++){
        const x=column*cellW;ctx.fillStyle=rgb(column%ribEvery===0?lighten(color,.12):darken(color,.22),.42);ctx.fillRect(x-cellW*.48,0,cellW*.96,height);
      }
      const scale=structure.includes('cardigan')?1.2:1;
      drawLoopGrid(ctx,{width,height,columns,rows:Math.round(rows/scale),color,lineWidth:lineWidth*(structure==='full-cardigan'?1.28:1.08),random,colorAt:(row,column,base)=>column%2?darken(base,.13):lighten(base,.06)});
      if(structure==='full-cardigan')drawHorizontalRidges(ctx,width,height,color,cellH*2.05,lineWidth*.8,random);
      return;
    }
    if(structure==='interlock'){
      drawLoopGrid(ctx,{width,height,columns,rows,color:darken(color,.08),lineWidth:lineWidth*.92,random});
      drawLoopGrid(ctx,{width,height,columns:columns-1,rows:rows-1,color:lighten(color,.12),lineWidth:lineWidth*.8,random,offset:cellH*.45});return;
    }
    if(structure==='milano'){
      drawLoopGrid(ctx,{width,height,columns,rows,color,lineWidth,random});drawHorizontalRidges(ctx,width,height,color,cellH*2.75,lineWidth*1.05,random);return;
    }
    if(structure==='pique'){
      drawLoopGrid(ctx,{width,height,columns,rows,color,lineWidth:lineWidth*.85,random,colorAt:(row,column,base)=>(row+column)%2?darken(base,.18):lighten(base,.14)});
      for(let row=0;row<rows;row+=2)for(let column=0;column<columns;column+=2){ctx.beginPath();ctx.arc(column*cellW+cellW*.5,row*cellH+cellH*.5,lineWidth*.44,0,Math.PI*2);ctx.fillStyle=rgb(lighten(color,.55),.32);ctx.fill()}
      return;
    }
    if(structure==='jacquard'){
      const accent=mix(color,{r:224,g:205,b:170},.62);
      drawLoopGrid(ctx,{width,height,columns,rows,color,lineWidth,random,colorAt:(row,column,base)=>((Math.floor(row/4)+Math.floor(column/5))%2)?accent:base});return;
    }
    if(structure==='cable'){
      drawLoopGrid(ctx,{width,height,columns,rows,color:darken(color,.08),lineWidth:lineWidth*.72,random});
      const bands=5,bandWidth=width/(bands+1);
      for(let band=1;band<=bands;band++){
        const center=band*bandWidth;
        for(let side=-1;side<=1;side+=2){ctx.beginPath();ctx.moveTo(center+side*bandWidth*.12,-20);for(let y=0;y<=height+40;y+=cellH*2){const phase=Math.floor(y/(cellH*2))%2?1:-1;ctx.bezierCurveTo(center+side*bandWidth*.42*phase,y+cellH*.55,center-side*bandWidth*.42*phase,y+cellH*1.45,center-side*bandWidth*.12,y+cellH*2)}ctx.strokeStyle=rgb(darken(color,.38),.72);ctx.lineWidth=lineWidth*2.8;ctx.lineCap='round';ctx.stroke();ctx.strokeStyle=rgb(lighten(color,.23),.88);ctx.lineWidth=lineWidth*1.65;ctx.stroke();ctx.strokeStyle=rgb(lighten(color,.75),.3);ctx.lineWidth=Math.max(1,lineWidth*.25);ctx.stroke()}
      }
      return;
    }
    drawLoopGrid(ctx,{width,height,columns,rows,color,lineWidth:structure==='full-needle'?lineWidth*.9:lineWidth,random});
  }

  function drawSurfaceEffects(ctx,width,height,color,features,random){
    ctx.save();
    for(let i=0;i<2800;i++){
      const x=random()*width,y=random()*height,r=random()*1.4+.2;
      ctx.fillStyle=random()>.52?rgb(lighten(color,.7),.055):rgb(darken(color,.75),.045);ctx.fillRect(x,y,r,r);
    }
    const hairs=Math.round(180+features.fuzz*1700);
    ctx.lineCap='round';
    for(let i=0;i<hairs;i++){
      const x=random()*width,y=random()*height,length=(3+random()*20)*features.fuzz,angle=(random()-.5)*Math.PI;
      ctx.beginPath();ctx.moveTo(x,y);ctx.quadraticCurveTo(x+Math.cos(angle)*length*.55,y+Math.sin(angle)*length*.55-2,x+Math.cos(angle)*length,y+Math.sin(angle)*length);
      ctx.strokeStyle=random()>.5?rgb(lighten(color,.75),.08+.11*features.fuzz):rgb(darken(color,.7),.055+.06*features.fuzz);ctx.lineWidth=.45+random()*.85;ctx.stroke();
    }
    if(features.irregular>.3){
      for(let i=0;i<320*features.irregular;i++){const x=random()*width,y=random()*height,length=4+random()*22;ctx.beginPath();ctx.moveTo(x,y);ctx.lineTo(x+length,y+(random()-.5)*3);ctx.strokeStyle=rgb(lighten(color,.7),.1);ctx.lineWidth=.6+random()*1.4;ctx.stroke()}
    }
    if(features.fancy>.25){
      for(let i=0;i<95*features.fancy;i++){const x=random()*width,y=random()*height,r=2+random()*7;ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.strokeStyle=rgb(random()>.3?lighten(color,.7):darken(color,.5),.24);ctx.lineWidth=1+random()*2;ctx.stroke()}
    }
    if(features.sheen>.25){
      const shine=ctx.createLinearGradient(0,height,width,0);shine.addColorStop(0,'rgba(255,255,255,0)');shine.addColorStop(.45,`rgba(255,255,255,${.035+features.sheen*.09})`);shine.addColorStop(.56,'rgba(255,255,255,0)');ctx.fillStyle=shine;ctx.fillRect(0,0,width,height);
    }
    const vignette=ctx.createRadialGradient(width*.5,height*.45,height*.08,width*.5,height*.5,width*.72);vignette.addColorStop(.56,'rgba(0,0,0,0)');vignette.addColorStop(1,'rgba(8,18,16,.28)');ctx.fillStyle=vignette;ctx.fillRect(0,0,width,height);ctx.restore();
  }

  function drawFabric(){
    if(!selectedYarn)return;
    const canvas=$('knitCanvas'),ctx=canvas.getContext('2d',{alpha:false});
    const width=canvas.width,height=canvas.height;
    const gauge=Number($('gauge').value),ends=Number($('knittingEnds').value),structure=$('knitStructure').value;
    const color=hexToRgb($('yarnColor').value);
    const seed=hashString([selectedYarn.id,selectedYarn.source,gauge,ends,structure,$('yarnColor').value,generationVariant].join('|'));
    const random=randomFactory(seed);
    const background=ctx.createLinearGradient(0,0,width,height);background.addColorStop(0,rgb(lighten(color,.12)));background.addColorStop(.52,rgb(color));background.addColorStop(1,rgb(darken(color,.24)));ctx.fillStyle=background;ctx.fillRect(0,0,width,height);
    drawPattern(ctx,width,height,structure,gauge,ends,color,random);
    drawSurfaceEffects(ctx,width,height,color,materialFeatures(selectedYarn),random);
    $('canvasPlaceholder').classList.add('hidden');
    $('downloadPng').disabled=false;
    $('generationFacts').innerHTML=[selectedYarn.name,`${gauge}G`,STRUCTURE_LABELS[structure],`${ends}本取り`,selectedYarn.count||'番手要確認',selectedYarn.composition||'混率要確認'].map(value=>`<span>${esc(value)}</span>`).join('');
    $('generationStatus').textContent='端末内で生成しました。マスター・受信箱・顧客公開データは変更していません。';
    $('generationStatus').className='status success';
  }

  function safeFileName(value){return String(value||'yarn').normalize('NFKC').replace(/[^a-zA-Z0-9一-龠ぁ-んァ-ン_-]+/g,'_').replace(/^_+|_+$/g,'').slice(0,48)||'yarn'}
  function downloadPng(){
    if($('downloadPng').disabled||!selectedYarn)return;
    $('knitCanvas').toBlob(blob=>{if(!blob)return;const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=`KC_knit_image_${safeFileName(selectedYarn.name)}_${$('gauge').value}G_${$('knitStructure').value}_${$('knittingEnds').value}ends.png`;link.rel='noopener';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),30000)},'image/png');
  }

  function selectFromUrl(){
    const params=new URLSearchParams(location.search),source=params.get('source'),id=params.get('id');
    if(!source||!id)return;
    const yarn=[...masterYarns,...catalogYarns].find(row=>row.source===source&&(row.id===id||row.code===id));
    if(yarn){$('sourceFilter').value=source;selectYarn(yarn,false)}
  }

  async function init(){
    masterYarns=loadMasterYarns();
    try{catalogYarns=await loadCatalogYarns()}catch(error){$('generationStatus').textContent=`カタログを読み込めませんでした：${error.message||error}`;$('generationStatus').className='status error'}
    renderYarnResults();selectFromUrl();
  }

  $('sourceFilter').addEventListener('change',renderYarnResults);
  $('yarnQuery').addEventListener('input',renderYarnResults);
  $('clearSearch').addEventListener('click',()=>{$('sourceFilter').value='all';$('yarnQuery').value='';renderYarnResults()});
  $('knitForm').addEventListener('submit',event=>{event.preventDefault();generationVariant+=1;drawFabric()});
  $('resetConditions').addEventListener('click',()=>{applyYarnDefaults();$('yarnColor').value='#9b765e';$('generationStatus').textContent=selectedYarn?'条件を初期値へ戻しました。生成ボタンを押してください。':'糸を選択すると生成できます。';$('generationStatus').className='status'});
  $('downloadPng').addEventListener('click',downloadPng);
  window.addEventListener('storage',event=>{if(event.key===V04_KEY){masterYarns=loadMasterYarns();renderYarnResults();if(selectedYarn?.source==='master'){const refreshed=masterYarns.find(yarn=>yarn.id===selectedYarn.id);if(refreshed)selectYarn(refreshed,false)}}});
  init();
})();
