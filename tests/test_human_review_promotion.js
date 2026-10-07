const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(process.env.HUMAN_REVIEW_SOURCE || path.join(root, 'brand-intelligence/index-current.html'), 'utf8');
const script = [...html.matchAll(/<script(?:\s[^>]*)?>(.*?)<\/script>/gs)].at(-1)[1];
const source = script.slice(0, script.indexOf("    $('openInbox').addEventListener")) +
  'globalThis.review={promote,approve,loadQueue,hold:typeof hold==="function"?hold:undefined};})();';
const original = JSON.parse(fs.readFileSync(path.join(root, 'data/manual-intake/2026-10-07-qiyuan-qysmart-comfy-batch11.json'))).items[0];
const copy = value => JSON.parse(JSON.stringify(value));
const MASTER = 'kc_independent_practical_v0_4';
const QUEUE = 'kc_v04_handoff_queue_v1';

function runtime(item = copy(original), state = {}, { failQueue = false, confirm = true } = {}) {
  const storage = new Map([[MASTER, JSON.stringify(state)], [QUEUE, JSON.stringify([item])]]);
  let failed = false;
  const nodes = new Map();
  const node = id => {
    if (!nodes.has(id)) nodes.set(id, { value: 'Test reviewer', textContent: '', innerHTML: '', classList: { toggle() {} }, contentWindow: { location: { reload() {} } } });
    return nodes.get(id);
  };
  const context = vm.createContext({
    localStorage: {
      getItem: key => storage.get(key) ?? null,
      setItem: (key, value) => { if (failQueue && key === QUEUE && !failed) { failed = true; throw Error('QuotaExceededError'); } storage.set(key, value); },
      removeItem: key => storage.delete(key)
    },
    document: { getElementById: node, querySelectorAll: () => [], querySelector: selector => ({ value: selector.includes('data-type') ? item.payload.targetType : '' }) },
    location: { origin: 'https://local.test' }, crypto: { randomUUID: () => 'test' }, CSS: { escape: value => value }, confirm: () => confirm
  });
  vm.runInContext(source, context);
  return { review: context.review, storage, item, node, state: () => JSON.parse(storage.get(MASTER)), queue: () => JSON.parse(storage.get(QUEUE)) };
}

test('current PENDING candidate retains confirmed counts, claim tags and both composition levels without confirming yarn or material', () => {
  const r = runtime();
  const before = copy(r.item);
  const { state, ids } = r.review.promote(r.item, 'yarn', '');
  const yarn = state.yarns[0];
  assert.equal(yarn.displayCount, '40s/1');
  assert.equal(yarn.countValue, '40');
  assert.equal(yarn.plyCount, 1);
  assert.equal(yarn.countSystem ?? '', '');
  assert.deepEqual(Array.from(yarn.functions), ['調湿', '吸湿発熱', '消臭']);
  assert.ok(yarn.functionalProperties.every(value => value.verification_status === 'supplier_claim' && value.test === ''));
  assert.equal(yarn.status, 'CANDIDATE');
  assert.equal(yarn.verificationStatus, 'candidate');
  assert.equal(yarn.composition ?? '', '');
  assert.equal(yarn.compositionStatus, 'unconfirmed');
  assert.equal(yarn.processingMethod ?? '', '');
  assert.equal(state.materials.length, 0);
  assert.equal(ids.materialId, undefined);
  assert.equal(state.photoCaptureIdMap[before.payload.commonIds.materialId], undefined);
  const evidence = copy(yarn.intakeEvidence[0].payload);
  assert.deepEqual(evidence, before.payload);
  assert.equal(evidence.yarnComposition.total, 100);
  assert.equal(evidence.fabricComposition.components[0].percent, 95);
  assert.equal(evidence.fabricComposition.components[1].countDisplay, '20D');
  assert.deepEqual(r.item, before);
  assert.equal(r.queue()[0].review_status, 'PENDING');
  assert.deepEqual(r.state(), {}); // promotion alone does not persist
});

test('bare strings and unsupported evidence remain available without becoming verified function tags', () => {
  const r = runtime();
  r.item.payload.functionalProperties = ['調湿', { name: '消臭', verification_status: 'test_confirmed' }];
  const yarn = r.review.promote(r.item, 'yarn', '').state.yarns[0];
  assert.equal((yarn.functions || []).length, 0);
  assert.deepEqual(copy(yarn.intakeEvidence[0].payload.functionalProperties), r.item.payload.functionalProperties);
});

test('AI source and explicit unconfirmed field cannot inherit a global confirmed status', () => {
  const r = runtime();
  r.item.payload.verificationStatus = 'confirmed';
  r.item.payload.fieldEvidence.countValue.status = 'unconfirmed';
  assert.equal(r.review.promote(r.item, 'yarn', '').state.yarns[0].countValue ?? '', '');
  r.item.payload.sourceType = 'ai_candidate';
  const yarn = r.review.promote(r.item, 'yarn', '').state.yarns[0];
  assert.equal(yarn.displayCount ?? '', '');
  assert.equal((yarn.functions || []).length, 0);
  assert.equal(yarn.status, 'CANDIDATE');
  assert.equal(yarn.verificationStatus, 'candidate');
});

test('independent material evidence is required; material composition never falls back to yarn/fabric composition', () => {
  const r = runtime();
  assert.throws(() => r.review.promote(r.item, 'material', ''), /素材/);
  assert.deepEqual(r.state(), {});
  Object.assign(r.item.payload, { materialName: 'Functional fiber identity independently checked', materialVerificationStatus: 'confirmed', materialEvidenceId: 'EV-independent' });
  const material = r.review.promote(r.item, 'material', '').state.materials[0];
  assert.equal(material.name, r.item.payload.materialName);
  assert.equal(material.composition ?? '', '');
  assert.equal((material.functionalProperties || []).length, 0);
  assert.equal(material.evidenceId, 'EV-independent');
  for (const missing of ['materialName', 'materialVerificationStatus', 'materialEvidenceId']) {
    const incomplete = copy(r.item);
    delete incomplete.payload[missing];
    assert.equal(runtime(incomplete).review.promote(incomplete, 'yarn', '').state.materials.length, 0);
  }
  const aiMaterial = copy(r.item);
  aiMaterial.payload.sourceType = 'ai_candidate';
  assert.equal(runtime(aiMaterial).review.promote(aiMaterial, 'yarn', '').state.materials.length, 0);
});

test('new event preserves existing confirmed data and source history while retaining unconfirmed incoming evidence', () => {
  const r = runtime();
  const first = r.review.promote(r.item, 'yarn', '');
  first.state.yarns[0].composition = 'Previously independently verified composition';
  first.state.yarns[0].compositionStatus = 'confirmed';
  first.state.yarns[0].processingMethod = 'Existing verified processing';
  first.state.yarns[0].status = 'CONFIRMED';
  first.state.yarns[0].verificationStatus = 'confirmed';
  first.state.yarns[0].notes = 'Existing source note';
  first.state.yarns[0].fieldEvidence.processingMethod = {status: 'confirmed', evidenceId: 'EV-old'};
  const next = copy(r.item);
  next.event_version = 2;
  next.payload.countValue = '';
  next.payload.countDisplay = '';
  next.payload.functionalProperties = [];
  next.payload.fieldEvidence.processingMethod = {status: 'unconfirmed', evidenceId: 'EV-new'};
  const r2 = runtime(next, copy(first.state));
  const second = r2.review.promote(next, 'yarn', '');
  assert.equal(second.ids.yarnId, first.ids.yarnId);
  assert.equal(second.state.yarns.length, 1);
  const yarn = second.state.yarns[0];
  assert.equal(yarn.displayCount, '40s/1');
  assert.equal(yarn.composition, first.state.yarns[0].composition);
  assert.equal(yarn.processingMethod, 'Existing verified processing');
  assert.equal(yarn.verificationStatus, 'confirmed');
  assert.ok(yarn.notes.includes('Existing source note'));
  assert.ok(yarn.notes.includes(next.payload.notes));
  assert.equal(yarn.fieldEvidence.processingMethod.evidenceId, 'EV-old');
  assert.equal(yarn.intakeEvidence.length, 2);
  assert.equal(yarn.intakeEvidence[1].payload.verificationStatus, 'candidate');
});

test('approval persists review separately; repeated approval of the same reviewed queue item does nothing', () => {
  const r = runtime();
  r.review.approve(r.item.handoff_id);
  assert.equal(r.queue()[0].review_status, 'APPROVED');
  assert.equal(r.state().yarns[0].verificationStatus, 'candidate');
  const before = [...r.storage];
  r.review.approve(r.item.handoff_id);
  assert.deepEqual([...r.storage], before);
});

test('cancel and hold keep PENDING and preserve all storage; failed queue write rolls back approval', () => {
  for (const options of [{ confirm: false }, { failQueue: true }]) {
    const r = runtime(copy(original), {}, options);
    const before = [...r.storage];
    r.review.hold(r.item.handoff_id);
    assert.deepEqual([...r.storage], before);
    r.review.approve(r.item.handoff_id);
    assert.deepEqual([...r.storage], before);
    assert.equal(r.queue()[0].review_status, 'PENDING');
  }
});


test('replaying the same event keeps stable IDs and one source snapshot', () => {
  const r = runtime();
  const first = r.review.promote(r.item, 'yarn', '');
  const r2 = runtime(copy(r.item), copy(first.state));
  const replay = r2.review.promote(r2.item, 'yarn', '');
  assert.equal(replay.ids.yarnId, first.ids.yarnId);
  assert.equal(replay.state.yarns.length, 1);
  assert.equal(replay.state.yarns[0].intakeEvidence.length, 1);
  assert.equal(replay.state.photoCaptureImports.length, 1);
});

test('legacy queued batch retains all source data without inventing confirmation; material approval stays pending', () => {
  const item = copy(original);
  item.payload.functionalProperties = ['調湿', '吸湿発熱', '消臭'];
  delete item.payload.fieldEvidence.countValue;
  delete item.payload.fieldEvidence.plyCount;
  item.payload.fieldEvidence.countDisplay.status = 'confirmed_visible_as_40s_1_on_user_photo_exhibition_swatch';
  const r = runtime(item);
  const yarn = r.review.promote(item, 'yarn', '').state.yarns[0];
  assert.equal(yarn.displayCount ?? '', '');
  assert.equal(yarn.verificationStatus, 'candidate');
  assert.deepEqual(copy(yarn.intakeEvidence[0].payload), item.payload);
  item.payload.targetType = 'material';
  const material = runtime(item);
  const before = [...material.storage];
  material.review.approve(item.handoff_id);
  assert.deepEqual([...material.storage], before);
  assert.equal(material.queue()[0].review_status, 'PENDING');
});


test('independently confirmed fields and single-level legacy composition still promote', () => {
  const r = runtime();
  Object.assign(r.item.payload, {verificationStatus: 'confirmed', compositionStatus: 'confirmed', compositionRaw: 'Viscose 80% / Polyester 20%', processingMethod: 'Verified processing', yarnStructure: 'Verified structure'});
  r.item.payload.fieldEvidence.yarnStructure = {status: 'confirmed', evidenceId: 'EV-structure'};
  r.item.payload.fieldEvidence.processingMethod = {status: 'confirmed', evidenceId: 'EV-processing'};
  r.item.payload.fieldEvidence.compositionRaw = {status: 'confirmed', evidenceId: 'EV-composition'};
  delete r.item.payload.yarnComposition;
  delete r.item.payload.fabricComposition;
  const yarn = r.review.promote(r.item, 'yarn', '').state.yarns[0];
  assert.equal(yarn.status, 'CONFIRMED');
  assert.equal(yarn.processingMethod, 'Verified processing');
  assert.equal(yarn.structure, 'Verified structure');
  assert.equal(yarn.composition, 'Viscose 80% / Polyester 20%');
});


test('incoming supplier claims cannot replace test-confirmed functions, evidence, or unrelated existing tags', () => {
  const r = runtime();
  const first = r.review.promote(r.item, 'yarn', '');
  const yarn = first.state.yarns[0];
  yarn.functionalProperties = [{name: '消臭', verification_status: 'test_confirmed', evidence_id: 'EV-test', test: 'Existing test report'}, {name: 'Existing function', verification_status: 'document_confirmed', evidence_id: 'EV-other'}];
  yarn.functions = ['消臭', 'Existing function'];
  yarn.sustainableAttributes = [{name: 'Existing sustainable', verification_status: 'test_confirmed', evidence_id: 'EV-sustainable'}];
  const incoming = copy(r.item);
  incoming.event_version = 2;
  incoming.payload.sustainableAttributes = [{name: 'Existing sustainable', verification_status: 'document_confirmed', evidence_id: 'EV-new'}];
  const next = runtime(incoming, copy(first.state)).review.promote(incoming, 'yarn', '').state.yarns[0];
  const deodorization = next.functionalProperties.find(item => item.name === '消臭');
  assert.equal(deodorization.verification_status, 'test_confirmed');
  assert.equal(deodorization.evidence_id, 'EV-test');
  assert.equal(deodorization.test, 'Existing test report');
  assert.ok(next.functions.includes('Existing function'));
  assert.ok(next.functionalProperties.some(item => item.name === 'Existing function'));
  assert.equal(next.sustainableAttributes[0].evidence_id, 'EV-sustainable');
});


test('explicit conflicting composition cannot inherit global confirmation or overwrite existing verified composition', () => {
  for (const status of ['conflicting', 'unconfirmed']) {
    const r = runtime();
    r.item.payload.compositionStatus = 'confirmed';
    r.item.payload.fieldEvidence.compositionRaw.status = status;
    const first = r.review.promote(r.item, 'yarn', '');
    assert.equal(first.state.yarns[0].composition ?? '', '');
    first.state.yarns[0].composition = 'Existing verified single-level composition';
    first.state.yarns[0].compositionStatus = 'confirmed';
    const next = runtime(copy(r.item), copy(first.state)).review.promote(r.item, 'yarn', '').state.yarns[0];
    assert.equal(next.composition, 'Existing verified single-level composition');
    assert.equal(next.compositionStatus, 'confirmed');
  }
});


test('independently reviewed material also retains stronger existing function evidence', () => {
  const r = runtime();
  Object.assign(r.item.payload, {materialName: 'QA verified material', materialVerificationStatus: 'confirmed', materialEvidenceId: 'EV-material'});
  const first = r.review.promote(r.item, 'material', '');
  first.state.materials[0].functionalProperties = [{name: 'QA function', verification_status: 'test_confirmed', evidence_id: 'EV-material-test'}];
  r.item.payload.materialFunctionalProperties = [{name: 'QA function', verification_status: 'supplier_claim', evidence_id: 'EV-material-claim'}];
  const next = runtime(copy(r.item), copy(first.state)).review.promote(r.item, 'material', '').state.materials[0];
  assert.equal(next.functionalProperties[0].verification_status, 'test_confirmed');
  assert.equal(next.functionalProperties[0].evidence_id, 'EV-material-test');
});

function verifiedExistingYarn() {
  return {yarns: [{id: 'YN-00000042', commonId: 'YN-00000042', countValue: '60', displayCount: '60s/1', composition: 'Verified old composition', compositionStatus: 'confirmed', status: 'CONFIRMED', verificationStatus: 'confirmed', fieldEvidence: {countValue: {status: 'confirmed', evidenceId: 'EV-old-count'}, compositionRaw: {status: 'confirmed', evidenceId: 'EV-old-composition'}}}], photoCaptureIdMap: {[original.payload.commonIds.yarnId]: 'YN-00000042'}};
}

test('AI-rejected values cannot replace evidence attached to retained confirmed values', () => {
  const item = copy(original);
  item.payload.sourceType = 'ai_candidate';
  item.payload.countValue = '100';
  item.payload.fieldEvidence.countValue = {status: 'confirmed', evidenceId: 'EV-AI-count'};
  const yarn = runtime(item, verifiedExistingYarn()).review.promote(item, 'yarn', '').state.yarns[0];
  assert.equal(yarn.countValue, '60');
  assert.equal(yarn.fieldEvidence.countValue.evidenceId, 'EV-old-count');
  const accepted = copy(original);
  accepted.payload.fieldEvidence.countValue = {status: 'confirmed', evidenceId: 'EV-new-adopted-count'};
  const updated = runtime(accepted, verifiedExistingYarn()).review.promote(accepted, 'yarn', '').state.yarns[0];
  assert.equal(updated.countValue, '40');
  assert.equal(updated.fieldEvidence.countValue.evidenceId, 'EV-new-adopted-count');
});

test('empty values and rejected composition cannot replace evidence for existing formal fields', () => {
  const item = copy(original);
  item.payload.countValue = '';
  item.payload.fieldEvidence.countValue = {status: 'confirmed', evidenceId: 'EV-empty-count'};
  item.payload.fieldEvidence.compositionRaw = {status: 'confirmed', evidenceId: 'EV-candidate-composition'};
  const yarn = runtime(item, verifiedExistingYarn()).review.promote(item, 'yarn', '').state.yarns[0];
  assert.equal(yarn.countValue, '60');
  assert.equal(yarn.composition, 'Verified old composition');
  assert.equal(yarn.fieldEvidence.countValue.evidenceId, 'EV-old-count');
  assert.equal(yarn.fieldEvidence.compositionRaw.evidenceId, 'EV-old-composition');
});

test('notes remain idempotent after A, B and replay of A, without splitting multiline source notes', () => {
  const a = copy(original); a.payload.notes = 'Note A\n\nOriginal second paragraph';
  const first = runtime(a).review.promote(a, 'yarn', '');
  const b = copy(a); b.event_version = 2; b.payload.notes = 'Note B';
  const second = runtime(b, copy(first.state)).review.promote(b, 'yarn', '');
  const replay = runtime(a, copy(second.state)).review.promote(a, 'yarn', '').state.yarns[0];
  assert.equal(replay.notes, a.payload.notes + '\n\n' + b.payload.notes);
  const replayB = runtime(b, copy({ ...second.state, yarns: [copy(replay)] })).review.promote(b, 'yarn', '').state.yarns[0];
  assert.equal(replayB.notes, replay.notes);
});

test('legacy confirmed basicYarnForm supplies structure only when its evidence is accepted', () => {
  const item = copy(original);
  item.payload.verificationStatus = 'confirmed';
  item.payload.yarnStructure = '';
  item.payload.basicYarnForm = 'spun blend';
  delete item.payload.fieldEvidence.yarnStructure;
  delete item.payload.fieldEvidence.basicYarnForm;
  const confirmed = runtime(item).review.promote(item, 'yarn', '').state.yarns[0];
  assert.equal(confirmed.structure, 'spun blend');
  for (const blocked of [{sourceType: 'ai_candidate'}, {verificationStatus: 'candidate'}, {fieldEvidence: {basicYarnForm: {status: 'unconfirmed', evidenceId: 'EV-form'}}}]) {
    const candidate = copy(item); Object.assign(candidate.payload, blocked);
    const yarn = runtime(candidate).review.promote(candidate, 'yarn', '').state.yarns[0];
    assert.equal(yarn.structure, '未確認');
  }
});
