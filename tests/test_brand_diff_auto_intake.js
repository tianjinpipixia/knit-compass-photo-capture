const fs=require('fs');
const vm=require('vm');
const assert=require('assert');

const storage={};
const global={
  console,
  localStorage:{
    getItem:key=>storage[key]??null,
    setItem:(key,value)=>{storage[key]=value}
  },
  fetch:async()=>({ok:false,status:404,text:async()=>''}),
  CustomEvent:class CustomEvent{constructor(type,init={}){this.type=type;this.detail=init.detail}},
  Date,
  Math,
  JSON,
  String,
  Array,
  Object,
  Set,
  Map,
  RegExp,
  Number,
  Boolean,
  Promise,
  window:{dispatchEvent:()=>{}},
  document:{readyState:'loading',addEventListener:()=>{}}
};
vm.createContext(global);
vm.runInContext(fs.readFileSync('brand-intelligence/brand-diff-auto-intake.js','utf8'),global);
const api=global.window.KCBrandDiffAutoIntake;
assert(api,'API not exposed');

const newRow={
  d:'2026-08-20',b:'index',name:'フェザースリーブニット',code:'NOT_CAPTURED',
  regular_price_yen:4979,sale_price_yen:null,composition_status:'NOT_CAPTURED_NO_ESTIMATION',
  function:[],color:'NOT_CAPTURED',state:'NEW',source:'https://store.world.co.jp/s/brand/index/category/WB/WB01/',
  dedupe:'index|フェザースリーブニット',p:'HOLD'
};
assert.strictEqual(api.hasMeaningfulSignal(newRow),true);
const handoff=api.productHandoff(newRow);
assert.strictEqual(handoff.review_status,'PENDING');
assert.strictEqual(handoff.automatic_master_promotion,'FORBIDDEN');
assert.strictEqual(handoff.payload.targetType,'product');
assert.strictEqual(handoff.payload.productUrl,'','category URL must not become formal product URL');
assert.strictEqual(handoff.payload.sourceUrl,newRow.source);
assert.strictEqual(handoff.payload.verificationStatus,'candidate');

const unchanged={...newRow,state:'LIGHT_SCAN_OBSERVED'};
assert.strictEqual(api.hasMeaningfulSignal(unchanged),false);
const p1=api.productFingerprint(newRow);
const p2=api.productFingerprint({...newRow,regular_price_yen:3990});
assert.notStrictEqual(p1,p2,'material field change should create a new fingerprint');

const nbb={
  d:'2026-08-20',id:'BR-00051',b:'NATURAL BEAUTY BASIC',s:'SOURCE_URL_MIGRATED',
  f:'現行公式ECがmix.tokyoであることを確認。追加生産予約にシルクブレンド半袖カーデ¥7,491等を確認したが索引鮮度が当日ではないため8/20新規とは断定しない。',
  m:'URL移行の情報切れリスクを解消しつつ予約ニットを継続観測。',
  n:'mix.tokyoを正本化しライブ予約状態を確認',u:'https://mix.tokyo/pages/naturalbeautybasic'
};
const nbbItem=api.nbbResearchHandoff(nbb);
assert.strictEqual(nbbItem.payload.targetType,'research');
assert.strictEqual(nbbItem.payload.sourceUrl,'https://mix.tokyo/pages/naturalbeautybasic');
assert.strictEqual(nbbItem.review_status,'PENDING');
assert.strictEqual(nbbItem.automatic_master_promotion,'FORBIDDEN');
assert(nbbItem.payload.notes.includes('当日新商品とは断定しない'));

const compacted=api.compactQueue([
  {...handoff,handoff_id:'P1',dedupe_key:'p1',review_status:'PENDING',sent_at:'2026-08-20T00:00:00Z'},
  {...handoff,handoff_id:'P1dup',dedupe_key:'p1',review_status:'PENDING',sent_at:'2026-08-19T00:00:00Z'},
  {...nbbItem,handoff_id:'R1',dedupe_key:'r1',review_status:'APPROVED',sent_at:'2026-08-18T00:00:00Z'},
]);
assert.strictEqual(compacted.filter(x=>x.dedupe_key==='p1').length,1);
assert.strictEqual(compacted.some(x=>x.review_status==='PENDING'),true);

console.log('brand-diff-auto-intake tests: PASS');
