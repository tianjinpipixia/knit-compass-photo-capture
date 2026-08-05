(() => {
  'use strict';

  if (window.__kcKnittingEndsFieldInstalled) return;
  window.__kcKnittingEndsFieldInstalled = true;

  const DB_NAME = 'kc_independent_photo_capture_v1_0';
  const FORM_ID = 'capture';
  const FIELD_NAME = 'knittingEnds';
  const SIDECAR_KEY = 'kc_photo_capture_knitting_ends_v1';
  const DATA_CONTRACT_VERSION = '1.1.1';
  const DISPLAY_VERSION = '1.2.4';

  let pendingRecordId = '';
  let hydrateInProgress = false;

  function normalizeEnds(value) {
    if (value === null || value === undefined || value === '') return null;
    const number = Number(value);
    return Number.isInteger(number) && number > 0 ? number : null;
  }

  function parseEndsFromGauge(value) {
    const match = String(value || '').match(/[×xX*＊]\s*(\d+)\s*(?:本)?/);
    return match ? normalizeEnds(match[1]) : null;
  }

  function stripEndsFromGauge(value) {
    return String(value || '').replace(/\s*[×xX*＊]\s*\d+\s*(?:本)?\s*$/, '').trim();
  }

  function loadSidecar() {
    try {
      const parsed = JSON.parse(localStorage.getItem(SIDECAR_KEY) || '{}');
      return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {};
    } catch {
      return {};
    }
  }

  function saveSidecar(value) {
    try {
      localStorage.setItem(SIDECAR_KEY, JSON.stringify(value));
    } catch {
      // The IndexedDB event remains the source of truth. The sidecar only restores UI values quickly.
    }
  }

  function rememberEnds(recordId, ends, version = 0) {
    if (!recordId) return;
    const sidecar = loadSidecar();
    sidecar[recordId] = {
      value: normalizeEnds(ends),
      version: Number(version || 0),
      updatedAt: new Date().toISOString()
    };
    saveSidecar(sidecar);
  }

  function rememberedEnds(recordId) {
    if (!recordId) return null;
    return normalizeEnds(loadSidecar()[recordId]?.value);
  }

  function installIndexedDbCapture() {
    const prototype = globalThis.IDBObjectStore?.prototype;
    if (!prototype || prototype.add.__kcKnittingEndsWrapped) return;

    const nativeAdd = prototype.add;
    function addWithKnittingEnds(value, key) {
      if (
        this?.name === 'events'
        && value
        && typeof value === 'object'
        && value.snapshot
        && typeof value.snapshot === 'object'
        && String(value.recordId || '').startsWith('KCI-CAPTURE')
      ) {
        const form = document.getElementById(FORM_ID);
        const field = form?.elements?.namedItem(FIELD_NAME);
        if (field instanceof HTMLInputElement) {
          const gaugeField = form.elements.namedItem('gauge');
          const gaugeValue = gaugeField instanceof HTMLInputElement ? gaugeField.value.trim() : value.snapshot.gauge;
          const gaugeEnds = parseEndsFromGauge(gaugeValue);
          const ends = normalizeEnds(field.value.trim()) || gaugeEnds;
          value.snapshot[FIELD_NAME] = ends;
          if (gaugeEnds) value.snapshot.gauge = stripEndsFromGauge(gaugeValue);
          value.snapshot.dataContractVersion = DATA_CONTRACT_VERSION;
          rememberEnds(value.recordId, ends, value.version);
        }
      }
      return Reflect.apply(nativeAdd, this, arguments);
    }
    addWithKnittingEnds.__kcKnittingEndsWrapped = true;
    prototype.add = addWithKnittingEnds;
  }

  function fieldMarkup() {
    const label = document.createElement('label');
    label.dataset.knittingEndsField = 'true';
    label.innerHTML = `本取り（編地）
      <input name="${FIELD_NAME}" type="number" min="1" step="1" inputmode="numeric" placeholder="例：2">
      <small class="hint">「12G×2」は、ゲージ＝12G／本取り＝2本として分けて登録します。</small>`;
    return label;
  }

  function setFieldValue(input, value) {
    const ends = normalizeEnds(value);
    if (ends && input.dataset.userEdited !== 'true' && !input.value) input.value = String(ends);
  }

  function readLatestSnapshot(recordId) {
    return new Promise((resolve) => {
      if (!recordId) {
        resolve(null);
        return;
      }
      const request = indexedDB.open(DB_NAME);
      request.onerror = () => resolve(null);
      request.onupgradeneeded = () => {
        request.transaction?.abort();
        resolve(null);
      };
      request.onsuccess = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains('events')) {
          database.close();
          resolve(null);
          return;
        }
        const transaction = database.transaction('events', 'readonly');
        const rowsRequest = transaction.objectStore('events').getAll();
        rowsRequest.onerror = () => {
          database.close();
          resolve(null);
        };
        rowsRequest.onsuccess = () => {
          const latest = (rowsRequest.result || [])
            .filter((row) => row.recordId === recordId)
            .sort((a, b) => Number(b.version || 0) - Number(a.version || 0))[0];
          database.close();
          resolve(latest?.snapshot || null);
        };
      };
    });
  }

  async function restoreExistingValue(input, recordId) {
    const remembered = rememberedEnds(recordId);
    if (remembered) {
      setFieldValue(input, remembered);
      return;
    }
    const snapshot = await readLatestSnapshot(recordId);
    if (!input.isConnected || input.dataset.userEdited === 'true') return;
    const ends = normalizeEnds(snapshot?.[FIELD_NAME]) || parseEndsFromGauge(snapshot?.gauge);
    setFieldValue(input, ends);
    if (ends) rememberEnds(recordId, ends, snapshot?.version);
  }

  function ensureField(form) {
    if (!form || form.elements.namedItem(FIELD_NAME)) return;
    const gauge = form.elements.namedItem('gauge');
    const anchor = gauge?.closest('label');
    if (!anchor) return;

    const label = fieldMarkup();
    anchor.insertAdjacentElement('afterend', label);
    const input = label.querySelector('input');
    input.addEventListener('input', () => {
      input.dataset.userEdited = 'true';
    });
    restoreExistingValue(input, pendingRecordId);
  }

  function decorateRecordCards() {
    const sidecar = loadSidecar();
    document.querySelectorAll('[data-edit]').forEach((button) => {
      const ends = normalizeEnds(sidecar[button.dataset.edit]?.value);
      const card = button.closest('.record');
      const tags = card?.querySelector('.mini-tags');
      if (!tags) return;
      const existing = tags.querySelector('[data-knitting-ends-tag]');
      if (!ends) {
        existing?.remove();
        return;
      }
      const tag = existing || document.createElement('span');
      tag.className = 'mini-tag';
      tag.dataset.knittingEndsTag = 'true';
      tag.textContent = `本取り ${ends}本`;
      if (!existing) tags.append(tag);
    });
  }

  async function hydrateSidecarFromEvents() {
    if (hydrateInProgress || !document.querySelector('[data-edit]')) return;
    hydrateInProgress = true;
    try {
      const request = indexedDB.open(DB_NAME);
      const database = await new Promise((resolve, reject) => {
        request.onerror = () => reject(request.error || new Error('DATABASE_OPEN_FAILED'));
        request.onupgradeneeded = () => {
          request.transaction?.abort();
          reject(new Error('DATABASE_NOT_READY'));
        };
        request.onsuccess = () => resolve(request.result);
      });
      if (!database.objectStoreNames.contains('events')) {
        database.close();
        return;
      }
      const rows = await new Promise((resolve, reject) => {
        const transaction = database.transaction('events', 'readonly');
        const rowsRequest = transaction.objectStore('events').getAll();
        rowsRequest.onerror = () => reject(rowsRequest.error || new Error('EVENTS_READ_FAILED'));
        rowsRequest.onsuccess = () => resolve(rowsRequest.result || []);
      });
      database.close();

      const latest = new Map();
      for (const row of rows) {
        const current = latest.get(row.recordId);
        if (!current || Number(row.version || 0) > Number(current.version || 0)) latest.set(row.recordId, row);
      }
      for (const [recordId, row] of latest) {
        const ends = normalizeEnds(row.snapshot?.[FIELD_NAME]) || parseEndsFromGauge(row.snapshot?.gauge);
        if (ends) rememberEnds(recordId, ends, row.version);
      }
      decorateRecordCards();
    } catch {
      // The application can still create and save records; hydration is only a display enhancement.
    } finally {
      hydrateInProgress = false;
    }
  }

  function refreshVersionDisclosure() {
    document.querySelectorAll('.connection-item').forEach((element) => {
      if ((element.textContent || '').startsWith('版:')) element.textContent = `版: v${DISPLAY_VERSION}`;
    });
    document.querySelectorAll('.badge').forEach((element) => {
      if (/^v1\.2\.3$/.test(element.textContent || '')) element.textContent = `v${DISPLAY_VERSION}`;
    });
    document.querySelectorAll('.eyebrow').forEach((element) => {
      if ((element.textContent || '').includes('Data Contract 1.1.0')) {
        element.textContent = (element.textContent || '').replace('Data Contract 1.1.0', `Data Contract ${DATA_CONTRACT_VERSION}`);
      }
    });
  }

  document.addEventListener('click', (event) => {
    const edit = event.target.closest?.('[data-edit]');
    if (edit) pendingRecordId = edit.dataset.edit || '';
    if (event.target.closest?.('#new')) pendingRecordId = '';
  }, true);

  const observer = new MutationObserver(() => {
    ensureField(document.getElementById(FORM_ID));
    refreshVersionDisclosure();
    decorateRecordCards();
    hydrateSidecarFromEvents();
  });

  installIndexedDbCapture();
  observer.observe(document.documentElement, { childList: true, subtree: true });
  ensureField(document.getElementById(FORM_ID));
  refreshVersionDisclosure();
  decorateRecordCards();
})();
