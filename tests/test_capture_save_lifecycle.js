const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(new URL('../app.js', `file://${__filename}`), 'utf8');
const saveSource = source.slice(source.indexOf('  async function saveDraft(event)'), source.indexOf('  function clearSearch()'));

function runtime({ fail = false, busy = false, processing = false } = {}) {
  const calls = [];
  const form = { elements: { human_review_status: { value: 'NOT_REVIEWED' } } };
  const snapshot = { supplier: 'Supplier A', visitContext: 'Show', photoRefs: [{ photoId: 'new-photo' }] };
  const state = {
    isSaving: busy, processingPhotos: new Set(processing ? ['photo'] : []), latestRecords: [],
    existingPhotoRefs: [], removedPhotoIds: new Set(), session: { accountId: 'test', displayName: 'Test' },
    db: { transaction: () => { calls.push('transaction'); return { objectStore: name => ({ add: () => calls.push(`add:${name}`) }) }; } }
  };
  const signals = [];
  const context = vm.createContext({
    state, MAX_PHOTOS_PER_RECORD: 10, STORES: { events: 'events', audit: 'audit', photos: 'photos' }, CONTRACT: { audit_store: 'audit' },
    clean: value => String(value || ''), createId: prefix => prefix + '-test', isoNow: () => '2026-09-06T08:00:00Z',
    preparePhotos: () => [{ ref: snapshot.photoRefs[0], record: { photoId: 'new-photo' } }],
    sortPhotoEntries: value => value, collectSnapshot: () => snapshot, hasDraftContent: () => true,
    missingCompanyRequiredFields: () => [], snapshotHash: async () => 'sha256',
    transactionPromise: async () => { if (fail) throw new Error('QuotaExceededError'); calls.push('committed'); },
    loadEvents: async () => calls.push('loaded'), refreshCandidateOptions: () => {}, renderRecords: () => {},
    closeEditor: () => calls.push('closed'), updateSaveButtonState: () => {},
    setMessage: (id, message, error) => calls.push({ id, message, error }),
    CustomEvent: class { constructor(type, init = {}) { this.type = type; this.detail = init.detail; } },
    document: { dispatchEvent: event => { signals.push(event); calls.push(event.type); } }
  });
  vm.runInContext(saveSource, context);
  return { calls, signals, state, save: () => context.saveDraft({ preventDefault() {}, currentTarget: form, submitter: { dataset: { saveDestination: 'LOCAL' } } }) };
}

test('save confirmation is emitted after transaction commit and editor close', async () => {
  const r = runtime();
  await r.save();
  assert.ok(r.calls.indexOf('committed') < r.calls.indexOf('closed'));
  assert.ok(r.calls.indexOf('closed') < r.calls.indexOf('kc:capture-saved'));
  assert.equal(r.signals[0].detail.supplier, 'Supplier A');
  assert.equal(r.signals[0].detail.photoCount, 1);
  assert.equal(r.signals[0].detail.eventType, 'CREATE');
  assert.deepEqual(r.signals.map(e => e.type), ['kc:capture-saved', 'kc:capture-save-finished']);
  assert.equal(r.state.isSaving, false);
});

test('failed storage keeps the editor and emits no successful-save event', async () => {
  const r = runtime({ fail: true });
  await r.save();
  assert.ok(!r.calls.includes('closed'));
  assert.ok(!r.calls.includes('kc:capture-saved'));
  assert.ok(r.calls.some(call => call.error && call.message.includes('QuotaExceededError')));
  assert.deepEqual(r.signals.map(e => e.type), ['kc:capture-save-finished']);
  assert.equal(r.state.isSaving, false);
});

test('duplicate submit and photo processing cannot start another transaction', async () => {
  for (const flags of [{ busy: true }, { processing: true }]) {
    const r = runtime(flags);
    await r.save();
    assert.ok(!r.calls.includes('transaction'));
    assert.equal(r.signals.length, 0);
  }
});
