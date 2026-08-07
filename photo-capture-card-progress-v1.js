(() => {
  'use strict';

  if (window.__kcPhotoCaptureCardProgressV1Installed) return;
  window.__kcPhotoCaptureCardProgressV1Installed = true;

  const DB_NAME = 'kc_independent_photo_capture_v1_0';
  const STORE_NAME = 'events';
  const SIDECAR_KEY = 'kc_photo_capture_knitting_ends_v1';
  const FACT_LABELS = ['番手', '混率', '本取り', '品質表示・規格', '対応ゲージ（目安）', '対応ゲージ'];

  let snapshotMap = new Map();
  let loading = false;
  let queued = false;

  function normalizeEnds(value) {
    if (value === null || value === undefined || value === '') return null;
    const number = Number(String(value).replace(/[^0-9]/g, ''));
    return Number.isInteger(number) && number > 0 ? number : null;
  }

  function parseEndsFromGauge(value) {
    const match = String(value || '').match(/[×xX*＊]\s*(\d+)\s*(?:本)?/);
    return match ? normalizeEnds(match[1]) : null;
  }

  function stripEndsFromGauge(value) {
    return String(value || '').replace(/\s*[×xX*＊]\s*\d+\s*(?:本)?\s*$/, '').trim();
  }

  function rememberedEnds(recordId) {
    if (!recordId) return null;
    try {
      const sidecar = JSON.parse(localStorage.getItem(SIDECAR_KEY) || '{}');
      return normalizeEnds(sidecar?.[recordId]?.value);
    } catch {
      return null;
    }
  }

  function displayCount(snapshot = {}) {
    const explicit = String(snapshot.countDisplay || '').trim();
    if (explicit) return explicit;
    const value = String(snapshot.countValue || snapshot.yarnCount || snapshot.yarn_count || '').trim();
    const system = String(snapshot.countSystem || '').trim();
    if (!value) return '';
    if (!system || system === 'unknown' || new RegExp(`\\b${system}\\b`, 'i').test(value)) return value;
    return `${value}${system}`;
  }

  function displayComposition(snapshot = {}) {
    return String(snapshot.compositionRaw || snapshot.composition || snapshot.composition_raw || '').trim();
  }

  function displayGauge(snapshot = {}) {
    return stripEndsFromGauge(snapshot.gauge || snapshot.gaugeDisplay || snapshot.gauge_display || '');
  }

  function displayEnds(recordId, snapshot = {}) {
    return normalizeEnds(snapshot.knittingEnds || snapshot.knitting_ends)
      || parseEndsFromGauge(snapshot.gauge || snapshot.gaugeDisplay || snapshot.gauge_display)
      || rememberedEnds(recordId);
  }

  function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME);
      request.onerror = () => reject(request.error || new Error('DATABASE_OPEN_FAILED'));
      request.onupgradeneeded = () => {
        request.transaction?.abort();
        reject(new Error('DATABASE_NOT_READY'));
      };
      request.onsuccess = () => resolve(request.result);
    });
  }

  async function readLatestSnapshots() {
    if (!globalThis.indexedDB || loading) return;
    loading = true;
    try {
      const database = await openDatabase();
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.close();
        return;
      }
      const rows = await new Promise((resolve, reject) => {
        const transaction = database.transaction(STORE_NAME, 'readonly');
        const request = transaction.objectStore(STORE_NAME).getAll();
        request.onerror = () => reject(request.error || new Error('EVENTS_READ_FAILED'));
        request.onsuccess = () => resolve(request.result || []);
      });
      database.close();
      const latest = new Map();
      for (const row of rows) {
        if (!row?.recordId) continue;
        const current = latest.get(row.recordId);
        if (!current || Number(row.version || 0) > Number(current.version || 0)) latest.set(row.recordId, row);
      }
      snapshotMap = new Map([...latest].map(([recordId, row]) => [recordId, row.snapshot || {}]));
    } catch {
      // 表示補助だけなので、正本データの読み込み失敗は既存UIを止めない。
    } finally {
      loading = false;
    }
  }

  function exactTextElement(root, text) {
    return [...root.querySelectorAll('*')].find((element) => {
      if (element.children.length) return false;
      return (element.textContent || '').trim() === text;
    }) || null;
  }

  function existingFactCard(root, label) {
    const labelElement = exactTextElement(root, label);
    if (!labelElement) return null;
    let candidate = labelElement.parentElement;
    while (candidate && candidate !== root) {
      if (candidate.matches('figure,.gallery,.photo-slot,.photos,[data-category]') || candidate.querySelector('img,figure')) return null;
      const text = (candidate.textContent || '').trim();
      if (text.length <= 180 && (candidate.children.length >= 2 || text !== label)) return { card: candidate, labelElement };
      candidate = candidate.parentElement;
    }
    return null;
  }

  function setExistingFactValue(fact, label, value) {
    if (!fact?.card || !fact.labelElement) return;
    fact.card.hidden = false;
    fact.labelElement.textContent = label;
    const valueElement = [...fact.card.children].find((child) => child !== fact.labelElement && (child.textContent || '').trim());
    if (valueElement) valueElement.textContent = value;
    else {
      const strong = document.createElement('strong');
      strong.textContent = value;
      fact.card.append(strong);
    }
  }

  function upgradeExistingFactCards(record, recordId, snapshot) {
    const oldSpecification = existingFactCard(record, '品質表示・規格');
    const existingEnds = existingFactCard(record, '本取り');
    const gaugeFact = existingFactCard(record, '対応ゲージ（目安）') || existingFactCard(record, '対応ゲージ');
    const ends = displayEnds(recordId, snapshot);
    const gauge = displayGauge(snapshot);

    if (oldSpecification || existingEnds) {
      const fact = existingEnds || oldSpecification;
      if (ends) setExistingFactValue(fact, '本取り', `${ends}本`);
      else fact.card.hidden = true;
      if (gaugeFact && gauge) setExistingFactValue(gaugeFact, gaugeFact.labelElement.textContent.trim(), gauge);
      return true;
    }
    return false;
  }

  function createFact(label, value, key) {
    const item = document.createElement('div');
    item.className = 'kc-yarn-fact';
    item.dataset.fact = key;
    const name = document.createElement('span');
    name.textContent = label;
    const strong = document.createElement('strong');
    strong.textContent = value;
    item.append(name, strong);
    return item;
  }

  function ensureRootFacts(record, recordId, snapshot) {
    if (FACT_LABELS.some((label) => exactTextElement(record, label))) return;
    const count = displayCount(snapshot);
    const composition = displayComposition(snapshot);
    const ends = displayEnds(recordId, snapshot);
    const gauge = displayGauge(snapshot);
    if (!count && !composition && !ends && !gauge) return;

    let facts = record.querySelector(':scope > .kc-yarn-facts');
    if (!facts) {
      facts = document.createElement('div');
      facts.className = 'kc-yarn-facts';
      const gallery = record.querySelector(':scope > .gallery');
      if (gallery) record.insertBefore(facts, gallery);
      else record.querySelector('.record-head')?.insertAdjacentElement('afterend', facts);
    }
    facts.replaceChildren();
    if (count) facts.append(createFact('番手', count, 'count'));
    if (composition) facts.append(createFact('混率', composition, 'composition'));
    if (ends) facts.append(createFact('本取り', `${ends}本`, 'knitting-ends'));
    if (gauge) facts.append(createFact('対応ゲージ（目安）', gauge, 'gauge'));
  }

  function recordIdFor(record) {
    return record.querySelector('[data-edit]')?.dataset.edit
      || record.dataset.recordId
      || record.getAttribute('data-record-id')
      || '';
  }

  function updateRecordFacts() {
    const recordCandidates = [...document.querySelectorAll('.record,[data-record-id]')];
    for (const record of recordCandidates) {
      const recordId = recordIdFor(record);
      const snapshot = snapshotMap.get(recordId) || {};
      if (upgradeExistingFactCards(record, recordId, snapshot)) continue;
      ensureRootFacts(record, recordId, snapshot);
    }
  }

  function findRestoreProgressCard() {
    const candidates = [...document.querySelectorAll('body *')].filter((element) => {
      if (element.matches('body,main')) return false;
      const text = (element.textContent || '').replace(/\s+/g, ' ').trim();
      return /写真\s*\d+\s*\/\s*\d+\s*枚/.test(text) && /復元・確認中/.test(text);
    });
    candidates.sort((a, b) => {
      const aProgress = a.querySelector('progress,[role="progressbar"]') ? 0 : 1;
      const bProgress = b.querySelector('progress,[role="progressbar"]') ? 0 : 1;
      if (aProgress !== bProgress) return aProgress - bProgress;
      return (a.textContent || '').length - (b.textContent || '').length;
    });
    return candidates[0] || null;
  }

  function findUploadControl() {
    return [...document.querySelectorAll('button,[role="button"],a')].find((element) => {
      const text = (element.textContent || '').replace(/\s+/g, ' ').trim();
      return /アップロード中/.test(text) || /受信箱へまとめてアップロード/.test(text) || /すべて受信箱へ送信済み/.test(text);
    }) || null;
  }

  function progressNumbers(text) {
    const count = text.match(/写真\s*(\d+)\s*\/\s*(\d+)\s*枚/);
    const percent = text.match(/(\d{1,3})\s*%/);
    const completed = count ? Number(count[1]) : 0;
    const total = count ? Number(count[2]) : 0;
    const calculated = total ? Math.round((completed / total) * 100) : 0;
    return { completed, total, percent: percent ? Math.min(100, Number(percent[1])) : calculated };
  }

  function progressHost(control) {
    if (!control) return null;
    const parent = control.parentElement;
    if (!parent) return null;
    if (parent.matches('.actions,.top-actions,.kc-actions,.upload-actions')) return parent;
    return parent;
  }

  function consolidateProgress() {
    const progressCard = findRestoreProgressCard();
    const control = findUploadControl();
    const existing = document.querySelector('[data-kc-unified-progress="true"]');

    if (!progressCard || !control || !/アップロード中/.test((control.textContent || '').trim())) {
      existing?.remove();
      document.querySelectorAll('[data-kc-progress-source-hidden="true"]').forEach((element) => {
        element.hidden = false;
        element.removeAttribute('data-kc-progress-source-hidden');
      });
      return;
    }

    const text = (progressCard.textContent || '').replace(/\s+/g, ' ').trim();
    const { completed, total, percent } = progressNumbers(text);
    const host = progressHost(control);
    if (!host) return;

    let unified = existing;
    if (!unified) {
      unified = document.createElement('div');
      unified.className = 'kc-unified-progress';
      unified.dataset.kcUnifiedProgress = 'true';
      unified.setAttribute('role', 'status');
      unified.setAttribute('aria-live', 'polite');
      unified.innerHTML = '<div class="kc-unified-progress-head"><strong data-kc-progress-title></strong><b data-kc-progress-percent></b></div><progress data-kc-progress-bar max="100" value="0"></progress><p>この画面を閉じずにお待ちください。</p>';
      host.insertAdjacentElement('afterend', unified);
    }
    unified.querySelector('[data-kc-progress-title]').textContent = `写真 ${completed} / ${total}枚を復元・確認中`;
    unified.querySelector('[data-kc-progress-percent]').textContent = `${percent}%`;
    const bar = unified.querySelector('[data-kc-progress-bar]');
    bar.value = percent;
    bar.setAttribute('aria-valuenow', String(percent));

    progressCard.hidden = true;
    progressCard.dataset.kcProgressSourceHidden = 'true';
  }

  const observer = new MutationObserver(() => {
    refresh();
  });

  function observe() {
    observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  }

  async function refresh() {
    if (queued) return;
    queued = true;
    await Promise.resolve();
    queued = false;
    await readLatestSnapshots();
    observer.disconnect();
    try {
      updateRecordFacts();
      consolidateProgress();
    } finally {
      observe();
    }
  }

  observe();
  refresh();
})();
