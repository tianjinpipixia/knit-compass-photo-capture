(() => {
  'use strict';

  if (window.KnitCompassMetrics) return;
  const STORAGE_KEY = 'kc_usage_metrics_v1';
  const FORMAT = 'KC_USAGE_METRICS';
  const MAX_DAYS = 120;
  const WORKFLOW_BY_PATH = [
    ['/owner-yarns/', 'yarn_search'],
    ['/market-intelligence/', 'raw_material_market'],
    ['/knit-image/', 'knit_image'],
    ['/fabric-inspection/', 'fabric_inspection'],
    ['/brand-intelligence/', 'product_research'],
    ['/customer-sharing/', 'customer_sharing'],
    ['/stylem/', 'customer_portal'],
    ['/daily/', 'daily'],
    ['/status/', 'system_admin']
  ];
  const workflow = WORKFLOW_BY_PATH.find(([path]) => location.pathname.includes(path))?.[1] || 'photo_capture';
  const localDate = () => {
    const value = new Date();
    value.setMinutes(value.getMinutes() - value.getTimezoneOffset());
    return value.toISOString().slice(0, 10);
  };
  const cleanToken = (value) => String(value || '').replace(/[^a-z0-9_-]/gi, '_').slice(0, 80) || 'unknown';

  const YARN_TAXONOMY_VERSION = '1.0.0';
  const COTTON_PREPARATION_OPTIONS = [
    ['unconfirmed', '未確認'],
    ['carded', 'カード／普梳棉／carded cotton'],
    ['combed', 'コーマ／精梳棉／combed cotton'],
    ['semi_combed', 'セミコーマ／半精梳／semi-combed'],
    ['other', 'その他']
  ];
  const SPINNING_METHOD_OPTIONS = [
    ['Unknown', '未確認'],
    ['Ring', 'リング紡績／环锭纺／ring spinning'],
    ['Compact', 'コンパクト紡績／紧密纺／compact spinning'],
    ['MVS', 'MVS・VORTEX／涡流纺／vortex spinning'],
    ['Air Jet', 'エアジェット紡績／喷气纺／air-jet spinning'],
    ['Open End', 'OE・ローター／气流纺・转杯纺／open-end・rotor'],
    ['Other', 'その他']
  ];
  const TAXONOMY_ALIASES = {
    carded: ['カード', 'カード綿', '普梳', '普梳棉', 'carded', 'carded cotton'],
    combed: ['コーマ', 'コーマ綿', '精梳', '精梳棉', 'combed', 'combed cotton'],
    semi_combed: ['セミコーマ', '半精梳', '半精梳棉', 'semi-combed', 'semi combed'],
    Ring: ['リング', 'リング紡績', '环锭纺', 'ring', 'ring spinning'],
    Compact: ['コンパクト', 'コンパクト紡績', '紧密纺', 'compact', 'compact spinning'],
    MVS: ['mvs', 'vortex', 'mvs・vortex', '涡流纺', '渦流紡'],
    'Air Jet': ['エアジェット', 'エアジェット紡績', '喷气纺', 'air-jet', 'air jet', 'air-jet spinning'],
    'Open End': ['oe', 'open end', 'open-end', 'ローター', 'ローター紡績', '气流纺', '转杯纺', 'rotor', 'rotor spinning']
  };
  const normalizeTaxonomyText = (value) => String(value || '').toLowerCase().replace(/[‐‑‒–—―]/g, '-').replace(/\s+/g, ' ').trim();
  const snapshotText = (snapshot) => normalizeTaxonomyText([
    snapshot?.yarnName, snapshot?.yarnCode, snapshot?.compositionRaw, snapshot?.yarnStructure,
    snapshot?.processingMethod, snapshot?.notes, snapshot?.sourceUrl
  ].filter(Boolean).join(' '));
  const hasAlias = (text, key) => (TAXONOMY_ALIASES[key] || []).some((alias) => text.includes(normalizeTaxonomyText(alias)));

  function detectCottonPreparation(snapshotOrText) {
    const text = typeof snapshotOrText === 'string' ? normalizeTaxonomyText(snapshotOrText) : snapshotText(snapshotOrText);
    if (hasAlias(text, 'semi_combed')) return 'semi_combed';
    if (hasAlias(text, 'combed')) return 'combed';
    if (hasAlias(text, 'carded')) return 'carded';
    return 'unconfirmed';
  }

  function detectSpinningMethod(snapshotOrText) {
    const text = typeof snapshotOrText === 'string' ? normalizeTaxonomyText(snapshotOrText) : snapshotText(snapshotOrText);
    for (const method of ['Compact', 'MVS', 'Air Jet', 'Open End', 'Ring']) {
      if (hasAlias(text, method)) return method;
    }
    return 'Unknown';
  }

  function emptyState() {
    return { format: FORMAT, schema_version: '1.0', privacy: 'DAILY_AGGREGATES_NO_INPUT_CONTENT', days: {} };
  }

  function load() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      return parsed?.format === FORMAT && parsed.days && typeof parsed.days === 'object' ? parsed : emptyState();
    } catch {
      return emptyState();
    }
  }

  function save(state) {
    const days = Object.keys(state.days).sort().slice(-MAX_DAYS);
    state.days = Object.fromEntries(days.map((day) => [day, state.days[day]]));
    state.updated_at = new Date().toISOString();
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* 利用画面を止めない */ }
  }

  function track(eventType, selectedWorkflow = workflow) {
    const state = load();
    const day = localDate();
    const key = `${cleanToken(selectedWorkflow)}.${cleanToken(eventType)}`;
    state.days[day] = state.days[day] || {};
    state.days[day][key] = Number(state.days[day][key] || 0) + 1;
    save(state);
    renderStatus();
  }

  function totals(state = load()) {
    const entries = Object.entries(state.days).sort(([a], [b]) => a.localeCompare(b));
    const totalEvents = entries.reduce((sum, [, metrics]) => sum + Object.values(metrics).reduce((part, count) => part + Number(count || 0), 0), 0);
    const searchCount = entries.reduce((sum, [, metrics]) => sum + Object.entries(metrics).filter(([key]) => key.endsWith('.search')).reduce((part, [, count]) => part + Number(count || 0), 0), 0);
    const submitCount = entries.reduce((sum, [, metrics]) => sum + Object.entries(metrics).filter(([key]) => key.endsWith('.form_submit')).reduce((part, [, count]) => part + Number(count || 0), 0), 0);
    return { activeDays: entries.length, totalEvents, searchCount, submitCount, lastDate: entries.at(-1)?.[0] || '記録なし' };
  }

  function csvCell(value) {
    let text = String(value ?? '');
    if (/^[=+\-@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  }

  function exportCsv() {
    const state = load();
    const headers = ['measurement_date','operator','workflow','event_type','item_type','item_id','registration_status','confirmed_at','baseline_minutes','actual_minutes','minutes_saved','ai_tool','ai_correction_count','human_review_status','evidence_id','evidence_status','reuse_count','active_user_count','notes'];
    const rows = [];
    Object.entries(state.days).sort(([a], [b]) => a.localeCompare(b)).forEach(([day, metrics]) => {
      Object.entries(metrics).sort(([a], [b]) => a.localeCompare(b)).forEach(([key, count]) => {
        const splitAt = key.indexOf('.');
        rows.push({
          measurement_date: day, operator: '', workflow: key.slice(0, splitAt), event_type: key.slice(splitAt + 1),
          item_type: 'usage_metric', item_id: '', registration_status: 'LOCAL_AGGREGATE', confirmed_at: '',
          baseline_minutes: '', actual_minutes: '', minutes_saved: '', ai_tool: '', ai_correction_count: '',
          human_review_status: '', evidence_id: '', evidence_status: 'DEVICE_AGGREGATE', reuse_count: count,
          active_user_count: 1, notes: '入力内容・氏名・検索語を保存しない日次集計'
        });
      });
    });
    const content = '\uFEFF' + [headers.join(','), ...rows.map((row) => headers.map((key) => csvCell(row[key])).join(','))].join('\r\n');
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `KC_usage_metrics_${localDate()}.csv`;
    link.rel = 'noopener';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  function renderStatus() {
    const target = document.getElementById('kcUsageSummary');
    if (!target) return;
    const value = totals();
    target.innerHTML = [
      ['記録日数', `${value.activeDays}日`], ['操作合計', `${value.totalEvents}件`],
      ['検索', `${value.searchCount}回`], ['登録操作', `${value.submitCount}回`], ['最終利用', value.lastDate]
    ].map(([label, count]) => `<div><span>${label}</span><strong>${count}</strong></div>`).join('');
    const button = document.getElementById('kcExportUsageMetrics');
    if (button) button.onclick = exportCsv;
  }

  function optionHtml(options, selected) {
    return options.map(([value, label]) => `<option value="${value}" ${value === selected ? 'selected' : ''}>${label}</option>`).join('');
  }

  function loadLatestPhotoCaptureSnapshot(form) {
    return new Promise((resolve) => {
      try {
        const request = indexedDB.open('kc_independent_photo_capture_v1_0');
        request.onerror = () => resolve(null);
        request.onsuccess = () => {
          const database = request.result;
          if (!database.objectStoreNames.contains('events')) { database.close(); resolve(null); return; }
          const tx = database.transaction('events', 'readonly');
          const all = tx.objectStore('events').getAll();
          all.onerror = () => { database.close(); resolve(null); };
          all.onsuccess = () => {
            const targetId = form.elements.targetId?.value?.trim();
            const yarnName = form.elements.yarnName?.value?.trim();
            const rows = (all.result || []).filter((event) => {
              const snapshot = event.snapshot || {};
              return (targetId && snapshot.targetId === targetId) || (yarnName && snapshot.yarnName === yarnName);
            }).sort((a, b) => Number(b.version || 0) - Number(a.version || 0));
            database.close();
            resolve(rows[0]?.snapshot || null);
          };
        };
      } catch { resolve(null); }
    });
  }

  async function enhancePhotoCaptureForm(form) {
    if (!form || form.dataset.kcYarnTaxonomy === '1') return;
    form.dataset.kcYarnTaxonomy = '1';
    const spinning = form.elements.spinningMethod;
    if (!spinning) return;
    const existingSnapshot = await loadLatestPhotoCaptureSnapshot(form);
    const existingMethod = existingSnapshot?.spinningMethod || spinning.value || 'Unknown';
    const knownMethods = new Set(SPINNING_METHOD_OPTIONS.map(([value]) => value));
    const options = knownMethods.has(existingMethod)
      ? SPINNING_METHOD_OPTIONS
      : [...SPINNING_METHOD_OPTIONS, [existingMethod, `${existingMethod}（既存データ互換）`]];
    spinning.innerHTML = optionHtml(options, existingMethod || 'Unknown');
    const spinningLabel = spinning.closest('label');
    if (spinningLabel?.firstChild?.nodeType === Node.TEXT_NODE) spinningLabel.firstChild.textContent = '最終紡績方式';

    const prepLabel = document.createElement('label');
    prepLabel.dataset.kcCottonPreparation = '1';
    prepLabel.innerHTML = `前紡・綿処理<select name="cottonPreparation">${optionHtml(COTTON_PREPARATION_OPTIONS, existingSnapshot?.cottonPreparation || detectCottonPreparation(existingSnapshot || {}))}</select><small class="hint">コーマ／精梳棉だけではリング紡績と推定しません。</small>`;
    spinningLabel?.before(prepLabel);
  }

  function installPhotoCaptureTaxonomy() {
    if (typeof IDBObjectStore !== 'undefined' && !IDBObjectStore.prototype.__kcYarnTaxonomyPatched) {
      const originalAdd = IDBObjectStore.prototype.add;
      Object.defineProperty(IDBObjectStore.prototype, '__kcYarnTaxonomyPatched', { value: true });
      IDBObjectStore.prototype.add = function patchedAdd(value, key) {
        if (this.name === 'events' && value?.snapshot) {
          const form = document.getElementById('capture');
          const snapshot = { ...value.snapshot };
          const selectedPreparation = form?.elements?.cottonPreparation?.value;
          const selectedSpinning = form?.elements?.spinningMethod?.value;
          snapshot.cottonPreparation = selectedPreparation || snapshot.cottonPreparation || detectCottonPreparation(snapshot);
          if (selectedSpinning) snapshot.spinningMethod = selectedSpinning;
          else if (!snapshot.spinningMethod || snapshot.spinningMethod === 'Unknown') snapshot.spinningMethod = detectSpinningMethod(snapshot);
          snapshot.yarnTaxonomyVersion = YARN_TAXONOMY_VERSION;
          value = { ...value, snapshot };
        }
        return originalAdd.call(this, value, key);
      };
    }
    const observe = () => {
      const form = document.getElementById('capture');
      if (form) enhancePhotoCaptureForm(form);
    };
    new MutationObserver(observe).observe(document.documentElement, { childList: true, subtree: true });
    observe();
  }

  const phraseReplacements = [
    [/combed\s+cotton/gi, '精梳'], [/carded\s+cotton/gi, '普梳'], [/semi[-\s]+combed/gi, '半精梳'],
    [/ring\s+spinning/gi, '环锭纺'], [/compact\s+spinning/gi, '紧密纺'], [/vortex\s+spinning/gi, '涡流纺'],
    [/air[-\s]+jet(?:\s+spinning)?/gi, '喷气纺'], [/open[-\s]+end/gi, '转杯纺'], [/rotor\s+spinning/gi, '转杯纺']
  ];
  const tokenAliasGroups = Object.values(TAXONOMY_ALIASES).map((aliases) => aliases.map(normalizeTaxonomyText));
  function normalizeSearchPhrase(value) {
    let result = String(value || '');
    phraseReplacements.forEach(([pattern, replacement]) => { result = result.replace(pattern, replacement); });
    return normalizeTaxonomyText(result);
  }
  function tokenAlternatives(token) {
    const normalized = normalizeTaxonomyText(token);
    const group = tokenAliasGroups.find((aliases) => aliases.includes(normalized));
    return group || [normalized];
  }
  function catalogHay(row) {
    return normalizeTaxonomyText([row.name, row.count_display, row.composition_raw, row.listed_supplier, row.source_id, row.spinning_method, row.cotton_preparation].filter(Boolean).join(' '));
  }
  function matchesTaxonomyQuery(row, query) {
    const hay = catalogHay(row);
    const tokens = normalizeSearchPhrase(query).split(/\s+/).filter(Boolean);
    return tokens.every((token) => tokenAlternatives(token).some((candidate) => hay.includes(candidate)));
  }

  function installOwnerYarnTaxonomySearch() {
    const toolbar = document.querySelector('.toolbar');
    const queryInput = document.getElementById('query');
    const applyButton = document.getElementById('applySearch');
    if (!toolbar || !queryInput || !applyButton || document.getElementById('kcCottonPreparationFilter')) return;

    const prep = document.createElement('label');
    prep.className = 'field';
    prep.innerHTML = `<span>前紡・綿処理</span><select id="kcCottonPreparationFilter">${optionHtml(COTTON_PREPARATION_OPTIONS, 'unconfirmed').replace('<option value="unconfirmed" selected>未確認</option>', '<option value="all" selected>すべて</option><option value="unconfirmed">未確認</option>')}</select>`;
    const spin = document.createElement('label');
    spin.className = 'field';
    spin.innerHTML = `<span>最終紡績方式</span><select id="kcSpinningMethodFilter"><option value="all">すべて</option>${optionHtml(SPINNING_METHOD_OPTIONS, '')}</select>`;
    toolbar.insertBefore(prep, applyButton);
    toolbar.insertBefore(spin, applyButton);
    queryInput.placeholder = '例：コーマ／精梳棉／combed cotton、VORTEX、1/24NM';

    let taxonomyCatalog = null;
    let taxonomyFiltered = [];
    let taxonomyVisible = 48;
    let taxonomyActive = false;
    const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;' }[c]));

    async function getCatalog() {
      if (taxonomyCatalog) return taxonomyCatalog;
      for (const url of ['../data/yarn-catalog/mz100-catalog-3000.json', '../data/yarn-catalog/mz100-catalog-2000.json']) {
        try {
          const response = await fetch(url, { cache: 'no-store' });
          const data = response.ok ? await response.json() : null;
          if (Array.isArray(data?.records) && data.records.length) { taxonomyCatalog = data.records; return taxonomyCatalog; }
        } catch { /* 次の候補 */ }
      }
      return [];
    }

    function rowTaxonomy(row) {
      const hay = catalogHay(row);
      return { preparation: row.cotton_preparation || detectCottonPreparation(hay), spinning: row.spinning_method || detectSpinningMethod(hay) };
    }

    function renderTaxonomyCatalog() {
      const grid = document.getElementById('catalogGrid');
      const resultCount = document.getElementById('resultCount');
      const loadMore = document.getElementById('loadMore');
      if (!grid || !resultCount || !loadMore) return;
      const rows = taxonomyFiltered.slice(0, taxonomyVisible);
      resultCount.textContent = `${taxonomyFiltered.length.toLocaleString('ja-JP')} / ${(taxonomyCatalog || []).length.toLocaleString('ja-JP')}件`;
      grid.innerHTML = rows.length ? rows.map((row) => {
        const taxonomy = rowTaxonomy(row);
        const prepLabel = new Map(COTTON_PREPARATION_OPTIONS).get(taxonomy.preparation) || '未確認';
        const spinLabel = new Map(SPINNING_METHOD_OPTIONS).get(taxonomy.spinning) || taxonomy.spinning || '未確認';
        return `<article class="card yarn-card"><div><div class="tags"><span class="tag">${esc(row.source)}</span><span class="tag pending">一覧掲載情報</span></div><h3>${esc(row.name)}</h3><div class="supplier">${esc(row.listed_supplier || '掲載供給元 要確認')}</div></div><div class="facts"><div><span>番手</span><strong>${esc(row.count_display || '要確認')}</strong></div><div><span>元ID</span><strong>${esc(row.source_id)}</strong></div><div><span>前紡・綿処理</span><strong>${esc(prepLabel)}</strong></div><div><span>最終紡績方式</span><strong>${esc(spinLabel)}</strong></div><div style="grid-column:1/-1"><span>掲載混率</span><strong>${esc(row.composition_raw || '要確認')}</strong></div></div><div class="tags"><span class="tag safe">検索候補</span><span class="tag pending">正式登録前</span></div><div class="actions"><a class="btn secondary" href="../knit-image/?source=catalog&amp;id=${encodeURIComponent(row.catalog_id)}">編み地イメージを作る</a><a class="source-link" href="${esc(row.source_url)}" target="_blank" rel="noopener">元ページを確認</a></div></article>`;
      }).join('') : '<div class="empty">条件に一致する糸がありません。</div>';
      loadMore.hidden = taxonomyVisible >= taxonomyFiltered.length;
    }

    async function applyTaxonomyFilters() {
      const rows = await getCatalog();
      const supplier = document.getElementById('supplier')?.value || 'all';
      const evidence = document.getElementById('evidence')?.value || 'all';
      const prepValue = document.getElementById('kcCottonPreparationFilter')?.value || 'all';
      const spinValue = document.getElementById('kcSpinningMethodFilter')?.value || 'all';
      taxonomyFiltered = rows.filter((row) => {
        if (queryInput.value.trim() && !matchesTaxonomyQuery(row, queryInput.value)) return false;
        if (supplier !== 'all' && row.listed_supplier !== supplier) return false;
        const composition = Boolean(row.composition_raw);
        const count = Boolean(row.count_display);
        if (evidence === 'composition' && !composition) return false;
        if (evidence === 'count' && !count) return false;
        if (evidence === 'both' && !(composition && count)) return false;
        const taxonomy = rowTaxonomy(row);
        if (prepValue !== 'all' && taxonomy.preparation !== prepValue) return false;
        if (spinValue !== 'all' && taxonomy.spinning !== spinValue) return false;
        return true;
      });
      taxonomyVisible = 48;
      taxonomyActive = true;
      renderTaxonomyCatalog();
    }

    document.addEventListener('click', (event) => {
      if (event.target.closest('#applySearch')) {
        event.preventDefault(); event.stopImmediatePropagation(); applyTaxonomyFilters(); track('taxonomy_search', 'yarn_search');
      } else if (event.target.closest('#resetSearch')) {
        event.preventDefault(); event.stopImmediatePropagation();
        queryInput.value = '';
        if (document.getElementById('supplier')) document.getElementById('supplier').value = 'all';
        if (document.getElementById('evidence')) document.getElementById('evidence').value = 'all';
        document.getElementById('kcCottonPreparationFilter').value = 'all';
        document.getElementById('kcSpinningMethodFilter').value = 'all';
        applyTaxonomyFilters();
      } else if (taxonomyActive && event.target.closest('#loadMore')) {
        event.preventDefault(); event.stopImmediatePropagation(); taxonomyVisible += 48; renderTaxonomyCatalog();
      }
    }, true);
    document.addEventListener('keydown', (event) => {
      if (event.target === queryInput && event.key === 'Enter') {
        event.preventDefault(); event.stopImmediatePropagation(); applyTaxonomyFilters(); track('taxonomy_search', 'yarn_search');
      }
    }, true);
    prep.querySelector('select').addEventListener('change', applyTaxonomyFilters);
    spin.querySelector('select').addEventListener('change', applyTaxonomyFilters);
  }

  if (workflow === 'photo_capture') installPhotoCaptureTaxonomy();
  if (workflow === 'yarn_search') {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', installOwnerYarnTaxonomySearch, { once: true });
    else installOwnerYarnTaxonomySearch();
  }

  const pageMarker = `kc_metric_page_${cleanToken(location.pathname)}`;
  try {
    if (!sessionStorage.getItem(pageMarker)) {
      sessionStorage.setItem(pageMarker, '1');
      track('page_open');
    }
  } catch {
    track('page_open');
  }

  const searchTimers = new WeakMap();
  document.addEventListener('input', (event) => {
    if (!(event.target instanceof HTMLInputElement) || event.target.type !== 'search') return;
    clearTimeout(searchTimers.get(event.target));
    searchTimers.set(event.target, setTimeout(() => track('search'), 700));
  }, true);
  document.addEventListener('submit', () => track('form_submit'), true);
  document.addEventListener('click', (event) => {
    const element = event.target.closest('button,a');
    if (!element) return;
    const action = element.dataset.kcMetric || ({
      new: 'capture_start', exportHandoff: 'handoff_export', kcExportBackup: 'backup_export',
      kcVerifyBackup: 'backup_verify', exportCompanyCsv: 'company_backup_export',
      generate: 'knit_image_generate', exportJson: 'audit_export'
    })[element.id];
    if (action) track(action);
  }, true);

  window.KnitCompassMetrics = Object.freeze({ track, totals, exportCsv, detectCottonPreparation, detectSpinningMethod });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderStatus, { once: true });
  else renderStatus();
})();
