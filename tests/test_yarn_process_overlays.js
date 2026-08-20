const fs=require('fs');
const vm=require('vm');
const assert=require('assert');

function rootContext(){
  class Store{constructor(){this.name='events'}add(v){return v}put(v){return v}}
  const window={};
  const document={documentElement:{},getElementById:()=>null,readyState:'complete'};
  class MutationObserver{constructor(){}observe(){}}
  const context={window,document,MutationObserver,IDBObjectStore:Store,indexedDB:{open(){throw new Error('not used')}},console,crypto:{}};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('yarn-process-fields-v1.js','utf8'),context);
  return context.window.KCYarnProcessFields;
}

const photo=rootContext();
assert.equal(photo.normalizePre('精梳棉'),'combed');
assert.equal(photo.normalizePre('半精梳'),'semi_combed');
assert.equal(photo.normalizePre('carded cotton'),'carded');
assert.equal(photo.normalizeSpin('Ring'),'ring');
assert.equal(photo.normalizeSpin('紧密纺'),'compact');
assert.equal(photo.normalizeSpin('MVS'),'mvs_vortex');
assert.equal(photo.normalizeSpin('喷气纺'),'air_jet');
assert.equal(photo.normalizeSpin('Open End'),'oe_rotor');
assert.equal(photo.normalizeSpin('Siro'),'other');

function masterContext(){
  const window={};
  const document={readyState:'loading',addEventListener:()=>{},getElementById:()=>null};
  const context={window,document,console,Blob:function(){},URL:{createObjectURL(){},revokeObjectURL(){}},setTimeout};
  vm.createContext(context);
  vm.runInContext(fs.readFileSync('brand-intelligence/yarn-process-master-v1.js','utf8'),context);
  return context.window.KCYarnProcessMaster;
}

const master=masterContext();
const state={yarns:[{id:'YN-1',name:'TEST',code:'A1',sourceCaptureId:'CAP-1'}]};
const queue=[{capture_id:'CAP-1',payload:{targetType:'yarn',yarnName:'TEST',yarnCode:'A1',preSpinningPreparation:'combed',spinningMethod:'MVS',spinningMethodRaw:'Supplier: MVS'}}];
master.applyPayloadFields(state,queue);
assert.equal(state.yarns[0].preSpinningPreparation,'combed');
assert.equal(state.yarns[0].spinningMethod,'mvs_vortex');
assert.equal(state.yarns[0].spinningMethodRaw,'Supplier: MVS');

console.log('yarn process overlay tests: PASS');
