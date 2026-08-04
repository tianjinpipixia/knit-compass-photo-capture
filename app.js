(() => {
  'use strict';

  const DB_NAME = 'kc_independent_photo_capture_v1_0';
  const SESSION_KEY = 'kc_session_v1';
  const HANDOFF_KEY = 'kc_v04_handoff_queue_v1';
  const HANDOFF_QUEUE_LIMIT = 500;
  const DATA_CONTRACT_VERSION = '1.1.0';
  const APP_VERSION = '1.2.2';
  const app = document.getElementById('app');

  const PHOTO_TYPES = [
    ['product', '表紙・全体'],
    ['yarn', '編地・糸・質感'],
    ['yarn_book', '混率・規格・色見本']
  ];
  const TARGET_TYPES = [
    ['yarn', '糸'], ['product', '商品'], ['material', '素材・原料'],
    ['organization', '会社・組織'], ['research', '調査記録']
  ];
  const SEASONS = ['春夏', '秋冬', '通年'];
  const FUNCTION_OPTIONS = [
    ['COOL_TOUCH', '接触冷感'], ['MOISTURE_QUICK_DRY', '吸水速乾'],
    ['UV_PROTECTION', 'UV・UPF'], ['HEAT_SHIELDING', '遮熱'],
    ['ANTIBACTERIAL', '抗菌・防臭'], ['ANTI_PILLING', '抗ピリング'],
    ['THERMAL_REGULATION', '調温'], ['ANTISTATIC', '帯電防止'], ['OTHER', 'その他']
  ];
  const SUSTAINABLE_OPTIONS = [
    ['RECYCLED', '再生原料'], ['BIO_BASED', 'バイオベース'],
    ['CERTIFIED_CELLULOSIC', '認証セルロース'], ['TRACEABLE', 'トレーサビリティ'],
    ['LOWER_IMPACT', '環境負荷低減'], ['OTHER', 'その他']
  ];
  const ID_PREFIX = { yarn: 'YN', product: 'PR', material: 'MT', organization: 'OR', research: 'RS' };

  let db;
  let session;
  let records = [];
  let editing = null;
  let pendingPhotos = {};
  let submitMode = 'draft';

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[character]);
  const nowIso = () => new Date().toISOString();
  const uuid = () => crypto.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  const internalId = (prefix) => `${prefix}-${uuid()}`;
  const temporaryCommonId = (type) => `TMP-${ID_PREFIX[type] || 'ID'}-${uuid()}`;
  const formatDate = (value) => value
    ? new Intl.DateTimeFormat('ja-JP', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
    : '—';

  function requestPromise(request) {
    return new Promise((resolve, reject) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('DATABASE_REQUEST_FAILED'));
    });
  }

  function transactionPromise(transaction) {
    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => resolve();
      transaction.onerror = transaction.onabort = () => reject(transaction.error || new Error('DATABASE_TRANSACTION_FAILED'));
    });
  }

  async function openDatabase() {
    db = await new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        const database = request.result;
        if (!database.objectStoreNames.contains('accounts')) database.createObjectStore('accounts', { keyPath: 'accountId' });
        if (!database.objectStoreNames.contains('events')) database.createObjectStore('events', { keyPath: 'eventId' });
        if (!database.objectStoreNames.contains('photos')) database.createObjectStore('photos', { keyPath: 'photoId' });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('DATABASE_OPEN_FAILED'));
    });
    session = JSON.parse(sessionStorage.getItem(SESSION_KEY) || 'null');
    if (session) renderApp(); else renderAuth();
  }

  async function getAll(storeName) {
    const transaction = db.transaction(storeName, 'readonly');
    const rows = await requestPromise(transaction.objectStore(storeName).getAll());
    await transactionPromise(transaction);
    return rows;
  }

  async function getOne(storeName, key) {
    const transaction = db.transaction(storeName, 'readonly');
    const row = await requestPromise(transaction.objectStore(storeName).get(key));
    await transactionPromise(transaction);
    return row;
  }

  async function passwordHash(password, salt, iterations = 180000) {
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', hash: 'SHA-256', salt, iterations }, key, 256);
    return [...new Uint8Array(bits)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  }

  function shell(body) {
    app.innerHTML = `<main class="app">${body}</main>`;
  }

  async function renderAuth() {
    const accounts = await getAll('accounts');
    const hasAccount = accounts.length > 0;
    shell(`<section class="card">
      <p class="eyebrow">Independent Workspace</p>
      <h1>Knit Compass Photo Capture</h1>
      <p class="lead">写真・撮影時情報・共通IDを独立Sandboxへ保存し、承認前データだけをv0.4受信箱へ渡します。</p>
      <div class="boundary"><span>Independent Account</span><span>IndexedDB保存</span><span>外部DB自動同期なし</span></div>
      <form id="auth" class="stack">
        ${hasAccount ? '' : '<label>表示名<input name="display" required placeholder="例：Knit Compass Owner"></label>'}
        <label>Independent Account ID<input name="account" required pattern="[A-Za-z0-9._-]{3,64}" placeholder="例：kc-owner"></label>
        <label>パスフレーズ<input name="pass" type="password" minlength="10" required><small class="hint">10文字以上。メールアドレスは不要です。</small></label>
        <button>${hasAccount ? '独立Workspaceへ入る' : '独立アカウントを作成'}</button>
      </form>
      <p id="authMessage" class="message">${hasAccount ? '登録済みアカウントで認証してください。' : '初回利用です。独立Sandbox専用アカウントを作成してください。'}</p>
    </section>`);

    document.getElementById('auth').addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const accountId = form.account.value.trim().toLowerCase();
      const password = form.pass.value;
      try {
        let account = await getOne('accounts', accountId);
        if (!hasAccount) {
          if (!form.display.value.trim()) throw new Error('表示名を入力してください');
          const salt = crypto.getRandomValues(new Uint8Array(16));
          account = {
            accountId,
            displayName: form.display.value.trim(),
            salt: [...salt],
            passHash: await passwordHash(password, salt),
            iterations: 180000
          };
          const transaction = db.transaction('accounts', 'readwrite');
          transaction.objectStore('accounts').add(account);
          await transactionPromise(transaction);
        } else if (!account || await passwordHash(password, new Uint8Array(account.salt), account.iterations) !== account.passHash) {
          throw new Error('IDまたはパスフレーズが違います');
        }
        session = { accountId: account.accountId, displayName: account.displayName };
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
        renderApp();
      } catch (error) {
        const message = document.getElementById('authMessage');
        message.textContent = `認証できませんでした: ${error.message}`;
        message.classList.add('error');
      }
    });
  }

  async function loadRecords() {
    const events = await getAll('events');
    const latest = new Map();
    events.sort((a, b) => Number(a.version) - Number(b.version)).forEach((event) => latest.set(event.recordId, event));
    records = [...latest.values()].sort((a, b) => String(b.updatedAt).localeCompare(String(a.updatedAt)));
    return events;
  }

  function handoffQueue() {
    try {
      const parsed = JSON.parse(localStorage.getItem(HANDOFF_KEY) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function handoffItemKey(item) {
    return item?.dedupe_key || item?.handoff_id || '';
  }

  function compactHandoffQueue(queue) {
    const ordered = [...queue].sort((a, b) => String(b.sent_at || '').localeCompare(String(a.sent_at || '')));
    const deduped = [];
    const seen = new Set();
    for (const item of ordered) {
      const key = handoffItemKey(item);
      if (key && seen.has(key)) continue;
      if (key) seen.add(key);
      deduped.push(item);
    }
    const pending = deduped.filter((item) => item.review_status === 'PENDING');
    const reviewed = deduped.filter((item) => item.review_status !== 'PENDING');
    const reviewedSlots = Math.max(0, HANDOFF_QUEUE_LIMIT - pending.length);
    return [...pending, ...reviewed.slice(0, reviewedSlots)]
      .sort((a, b) => String(b.sent_at || '').localeCompare(String(a.sent_at || '')));
  }

  function saveHandoffQueue(queue) {
    const compacted = compactHandoffQueue(queue);
    try {
      localStorage.setItem(HANDOFF_KEY, JSON.stringify(compacted));
    } catch (error) {
      alert('受信箱を保存できませんでした。未承認データは削除していません。受信箱JSONを書き出してから端末容量を確認してください。');
      throw error;
    }
    return { saved: compacted.length, prunedReviewed: Math.max(0, queue.length - compacted.length) };
  }

  function handoffCounts() {
    const queue = handoffQueue();
    return {
      total: queue.length,
      pending: queue.filter((item) => item.review_status === 'PENDING').length,
      approved: queue.filter((item) => item.review_status === 'APPROVED').length,
      rejected: queue.filter((item) => item.review_status === 'REJECTED').length
    };
  }

  function photosHtml(photoRefs = []) {
    const byType = new Map(photoRefs.map((reference) => [reference.type, reference]));
    return PHOTO_TYPES.map(([type, label]) => {
      const reference = byType.get(type);
      return `<figure>${reference
        ? `<div class="placeholder" data-photo="${escapeHtml(reference.photoId)}">読込中...</div>`
        : `<div class="placeholder">${label}<br>未登録</div>`}<figcaption>${label}</figcaption></figure>`;
    }).join('');
  }

  async function hydratePhotos() {
    for (const element of document.querySelectorAll('[data-photo]')) {
      const row = await getOne('photos', element.dataset.photo);
      if (row?.blob) {
        const url = URL.createObjectURL(row.blob);
        const image = new Image();
        image.src = url;
        image.alt = row.label || '写真';
        element.replaceWith(image);
      }
    }
  }

  function latestHandoffForCapture(captureId) {
    return handoffQueue().find((item) => item.capture_id === captureId) || null;
  }

  async function renderApp() {
    const events = await loadRecords();
    const counts = handoffCounts();
    shell(`<section class="card top">
      <div><p class="eyebrow">Independent Workspace / Data Contract ${DATA_CONTRACT_VERSION}</p><h1>Knit Compass Photo Capture</h1><p class="lead">混率・機能性・サステナブル・共通IDを同じDRAFTに保持し、Human Review前の候補としてv0.4受信箱へ渡します。</p></div>
      <div class="badges"><span class="badge">v${APP_VERSION}</span><span class="badge">DRAFT FIRST</span><span class="badge">共通ID</span><span class="badge off">外部DBなし</span></div>
      <div class="identity"><span>${escapeHtml(session.displayName)} / ${escapeHtml(session.accountId)}</span><button class="ghost" id="logout">終了</button></div>
    </section>

    <section class="card" id="inbox">
      <p class="eyebrow">Capture Inbox</p>
      <h2>Photo Capture</h2>
      <p class="lead">CREATE／UPDATEはAppend Onlyです。受信箱へ送っても、Human Review承認まではマスターへ反映しません。</p>
      <div class="actions top-actions"><button id="new">新規キャプチャ</button><button class="secondary" id="exportHandoff">受信箱JSONを書き出す</button><a class="button-link secondary" href="brand-intelligence/">v0.4受信箱を開く</a></div>
      <div class="kpis">
        <div class="kpi"><span>全レコード</span><strong>${records.length}</strong></div>
        <div class="kpi"><span>受信箱待ち</span><strong>${counts.pending}</strong></div>
        <div class="kpi"><span>承認済み</span><strong>${counts.approved}</strong></div>
        <div class="kpi"><span>UPDATE履歴</span><strong>${events.filter((event) => event.eventType === 'UPDATE').length}</strong></div>
      </div>
      <div class="toolbar"><input id="query" type="search" placeholder="共通ID、Supplier、糸名、品番、混率を検索"><button class="secondary" id="clear">検索をクリア</button></div>
      <div id="list"></div>
    </section>
    <section class="card hidden" id="editor"></section>`);

    document.getElementById('logout').addEventListener('click', () => {
      sessionStorage.removeItem(SESSION_KEY);
      session = null;
      renderAuth();
    });
    document.getElementById('new').addEventListener('click', () => openEditor());
    document.getElementById('query').addEventListener('input', renderList);
    document.getElementById('clear').addEventListener('click', () => {
      document.getElementById('query').value = '';
      renderList();
    });
    document.getElementById('exportHandoff').addEventListener('click', exportHandoffQueue);
    renderList();
  }

  function listTags(snapshot) {
    const tags = [];
    if (snapshot.compositionRaw) tags.push(snapshot.compositionRaw);
    for (const item of snapshot.functionalProperties || []) tags.push(item.name);
    for (const item of snapshot.sustainableAttributes || []) tags.push(item.name);
    return tags.slice(0, 6).map((tag) => `<span class="mini-tag">${escapeHtml(tag)}</span>`).join('');
  }

  function renderList() {
    const output = document.getElementById('list');
    if (!output) return;
    const query = (document.getElementById('query')?.value || '').toLowerCase();
    const rows = records.filter((event) => JSON.stringify(event.snapshot).toLowerCase().includes(query));
    output.innerHTML = rows.length ? `<div class="record-list">${rows.map((event) => {
      const row = event.snapshot;
      const handoff = latestHandoffForCapture(row.captureId || event.recordId);
      const status = handoff?.review_status || '未送信';
      return `<article class="record">
        <div class="record-head"><div><span class="target-pill">${escapeHtml(targetLabel(row.targetType))}</span><h3>${escapeHtml(row.yarnName || row.productName || row.sourceOrganizationName || row.materialName || '名称未入力のDRAFT')}</h3><p class="muted">${escapeHtml(row.targetId || '共通ID未発行')} / ${escapeHtml(row.sourceOrganizationName || row.supplier || '入手先未入力')}</p></div><span class="priority">${escapeHtml(row.priority || 'NORMAL')}</span></div>
        <div class="gallery">${photosHtml(row.photoRefs)}</div>
        <div class="mini-tags">${listTags(row)}</div>
        <div class="meta"><span>DRAFT</span><span>${escapeHtml(event.eventType)} v${event.version}</span><span>受信箱: ${escapeHtml(status)}</span><span>${escapeHtml(formatDate(event.updatedAt))}</span></div>
        <div class="actions"><button class="secondary" data-edit="${escapeHtml(event.recordId)}">編集・再保存</button><button data-send="${escapeHtml(event.recordId)}">v0.4受信箱へ送る</button></div>
      </article>`;
    }).join('')}</div>` : '<div class="empty"><h3>まだキャプチャはありません</h3><p class="muted">新規キャプチャから最初のDRAFTを作成してください。</p></div>';

    output.onclick = (event) => {
      const edit = event.target.closest('[data-edit]');
      const send = event.target.closest('[data-send]');
      if (edit) openEditor(edit.dataset.edit);
      if (send) enqueueExisting(send.dataset.send);
    };
    hydratePhotos();
  }

  function targetLabel(type) {
    return TARGET_TYPES.find(([value]) => value === type)?.[1] || '未分類';
  }

  function photoSlot(type, label) {
    return `<div class="photo-slot"><h3>${label}</h3><label>${label}を選択<input type="file" accept="image/*" capture="environment" data-input="${type}"></label><div class="preview" data-preview="${type}"><div class="placeholder">写真はまだ選択されていません</div></div></div>`;
  }

  function checkboxGroup(name, options, selected = []) {
    const selectedSet = new Set(selected);
    return options.map(([value, label]) => `<label class="check-option"><input type="checkbox" name="${name}" value="${value}" ${selectedSet.has(value) ? 'checked' : ''}><span>${label}</span></label>`).join('');
  }

  function selectOptions(options, selected = '') {
    return options.map(([value, label]) => `<option value="${escapeHtml(value)}" ${value === selected ? 'selected' : ''}>${escapeHtml(label)}</option>`).join('');
  }

  async function openEditor(recordId = '') {
    editing = records.find((event) => event.recordId === recordId) || null;
    pendingPhotos = {};
    submitMode = 'draft';
    const row = editing?.snapshot || {};
    const editor = document.getElementById('editor');
    editor.classList.remove('hidden');
    editor.innerHTML = `<div class="editor">
      <div><p class="eyebrow">Draft Editor / Append Only</p><h2>${editing ? 'DRAFTを編集' : '新規キャプチャ'}</h2><p class="lead">共通IDは名称変更後も維持します。未確定の場合は一時IDを自動発行し、Human Review承認時に正式IDへ昇格します。</p></div>
      <form id="capture">
        <section class="section">
          <h3>1. 対象と共通ID</h3>
          <div class="form-grid">
            <label>重要度<select name="priority"><option>NORMAL</option><option>HIGH</option><option>URGENT</option></select></label>
            <label>対象種別<select name="targetType">${selectOptions(TARGET_TYPES, row.targetType || 'yarn')}</select></label>
            <label class="wide">対象共通ID<input name="targetId" value="${escapeHtml(row.targetId || '')}" placeholder="未入力なら TMP-YN-… 等を自動発行"></label>
            <label>商品ID<input name="productId" value="${escapeHtml(row.commonIds?.productId || '')}" placeholder="PR-00000000"></label>
            <label>糸ID<input name="yarnId" value="${escapeHtml(row.commonIds?.yarnId || '')}" placeholder="YN-00000000"></label>
            <label>素材ID<input name="materialId" value="${escapeHtml(row.commonIds?.materialId || '')}" placeholder="MT-0000000"></label>
            <label>調査ID<input name="researchId" value="${escapeHtml(row.commonIds?.researchId || '')}" placeholder="RS-0000000000"></label>
          </div>
        </section>

        <section class="section"><h3>2. 写真</h3><div class="photo-grid">${PHOTO_TYPES.map((item) => photoSlot(...item)).join('')}</div></section>

        <section class="section">
          <h3>3. 入手先・会社</h3>
          <div class="form-grid">
            <label>入手先名<input name="sourceOrganizationName" value="${escapeHtml(row.sourceOrganizationName || row.supplier || '')}"></label>
            <label>入手先ID<input name="sourceOrganizationId" value="${escapeHtml(row.sourceOrganizationId || '')}" placeholder="OR-0000000 / 未確定可"></label>
            <label>メーカー名<input name="manufacturerName" value="${escapeHtml(row.manufacturerName || '')}"></label>
            <label>メーカーID<input name="manufacturerId" value="${escapeHtml(row.manufacturerId || '')}" placeholder="OR-0000000"></label>
            <label>販売会社名<input name="sellerName" value="${escapeHtml(row.sellerName || '')}"></label>
            <label>販売会社ID<input name="sellerId" value="${escapeHtml(row.sellerId || '')}" placeholder="OR-0000000"></label>
          </div>
        </section>

        <section class="section">
          <h3>4. 商品・糸の基本情報</h3>
          <div class="form-grid">
            <label>ブランド名<input name="brandName" value="${escapeHtml(row.brandName || '')}"></label>
            <label>商品名<input name="productName" value="${escapeHtml(row.productName || '')}"></label>
            <label>商品品番<input name="productCode" value="${escapeHtml(row.productCode || '')}"></label>
            <label>商品公式URL<input name="productUrl" type="url" value="${escapeHtml(row.productUrl || '')}"></label>
            <label>糸名<input name="yarnName" value="${escapeHtml(row.yarnName || '')}"></label>
            <label>糸品番・略称<input name="yarnCode" value="${escapeHtml(row.yarnCode || row.abbreviation || '')}"></label>
            <label>番手体系<select name="countSystem">${selectOptions([['Nm', '毛番手 Nm'], ['Ne', '綿番手 Ne'], ['D', 'デニール D'], ['dtex', 'dtex'], ['tex', 'tex'], ['unknown', '未確認']], row.countSystem || 'Nm')}</select></label>
            <label>番手値<input name="countValue" value="${escapeHtml(row.countValue || row.yarnCount || '')}" placeholder="例：30/2 または 30"></label>
            <label>表示番手<input name="countDisplay" value="${escapeHtml(row.countDisplay || '')}" placeholder="例：2/30 Nm"></label>
            <label>対応ゲージ<input name="gauge" value="${escapeHtml(row.gauge || '')}" placeholder="12G, 14G 等"></label>
            <label>基本糸形態<select name="basicYarnForm">${selectOptions([['unconfirmed', '未確認'], ['single', '単一紡績／単糸'], ['plied', '合撚'], ['combined', '交撚'], ['core_spun', 'コアスパン'], ['covered', 'カバリング'], ['fancy', 'ファンシー'], ['other', 'その他']], row.basicYarnForm || 'unconfirmed')}</select></label>
            <label>糸構造<input name="yarnStructure" value="${escapeHtml(row.yarnStructure || row.actualCountStructure || '')}" placeholder="DCY、芯糸、押さえ糸等"></label>
            <label>紡績方式<select name="spinningMethod">${selectOptions([['', ''], ['Ring', 'Ring'], ['Compact', 'Compact'], ['Siro', 'Siro'], ['MVS', 'MVS'], ['Open End', 'Open End'], ['Filament', 'Filament'], ['Fancy Yarn', 'Fancy Yarn'], ['Unknown', '未確認']], row.spinningMethod || '')}</select></label>
            <label>加工方法<input name="processingMethod" value="${escapeHtml(row.processingMethod || '')}"></label>
          </div>
        </section>

        <section class="section">
          <h3>5. 混率</h3>
          <div class="form-grid">
            <label class="wide">混率（品質表示どおり）<textarea name="compositionRaw" placeholder="例：再生繊維（セルロース）65%、レーヨン20%、ナイロン15%">${escapeHtml(row.compositionRaw || '')}</textarea></label>
            <label>確認状態<select name="compositionStatus">${selectOptions([['unconfirmed', '未確認'], ['candidate', '候補'], ['inferred', '推定'], ['confirmed', '確認済み'], ['conflicting', '矛盾あり']], row.compositionStatus || 'unconfirmed')}</select></label>
            <div class="composition-check"><span>合計チェック</span><strong id="compositionTotal">—</strong><small id="compositionMessage">数値を入力すると合計を確認します。</small></div>
          </div>
        </section>

        <section class="section">
          <h3>6. 機能性</h3>
          <div class="check-grid">${checkboxGroup('functionCodes', FUNCTION_OPTIONS, (row.functionalProperties || []).map((item) => item.code))}</div>
          <div class="form-grid">
            <label class="wide">機能性の補足<input name="functionDetail" value="${escapeHtml(row.functionDetail || '')}" placeholder="試験値、商品訴求、Supplier説明等"></label>
            <label>根拠状態<select name="functionClaimStatus">${selectOptions([['not_confirmed', '未確認'], ['supplier_claim', 'Supplier主張'], ['document_confirmed', '資料確認'], ['test_confirmed', '試験確認']], row.functionClaimStatus || 'not_confirmed')}</select></label>
            <label>試験方法・値<input name="functionTest" value="${escapeHtml(row.functionTest || '')}" placeholder="JIS、Q-MAX、UPF等"></label>
          </div>
        </section>

        <section class="section">
          <h3>7. サステナブル</h3>
          <div class="check-grid">${checkboxGroup('sustainableCodes', SUSTAINABLE_OPTIONS, (row.sustainableAttributes || []).map((item) => item.code))}</div>
          <div class="form-grid">
            <label class="wide">根拠・認証・規格<input name="sustainableBasis" value="${escapeHtml(row.sustainableBasis || '')}" placeholder="再生原料、FSC/PEFC、GRS、バイオベース比率等"></label>
            <label>確認状態<select name="sustainableStatus">${selectOptions([['unconfirmed', '未確認'], ['candidate', '候補'], ['inferred', '推定'], ['confirmed', '確認済み'], ['conflicting', '矛盾あり']], row.sustainableStatus || 'unconfirmed')}</select></label>
            <label>認証番号・標準<input name="certification" value="${escapeHtml(row.certification || '')}"></label>
          </div>
        </section>

        <section class="section">
          <h3>8. シーズン・根拠</h3>
          <div class="form-grid">
            <fieldset class="wide"><legend>シーズン</legend><div class="seasons">${SEASONS.map((season) => `<label><input type="checkbox" name="season" value="${season}" ${(row.seasons || []).includes(season) ? 'checked' : ''}>${season}</label>`).join('')}</div></fieldset>
            <label>資料区分<select name="documentType">${selectOptions([['color_book', 'カラーBOOK'], ['swatch', '編地・スワッチ'], ['product_sample', '製品サンプル'], ['raw_material', '原料'], ['catalog', 'カタログ'], ['exhibition', '展示会資料'], ['other', 'その他']], row.documentType || 'swatch')}</select></label>
            <label>情報源種別<select name="sourceType">${selectOptions([['physical', '現物確認'], ['official', '公式資料・URL'], ['supplier', 'Supplier資料'], ['wechat', 'WeChat'], ['ai_candidate', 'AI候補'], ['other', 'その他']], row.sourceType || 'physical')}</select></label>
            <label class="wide">情報源URL・資料参照<input name="sourceUrl" value="${escapeHtml(row.sourceUrl || '')}"></label>
            <label>全体確認状態<select name="verificationStatus">${selectOptions([['unconfirmed', '未確認'], ['candidate', '候補'], ['inferred', '推定'], ['confirmed', '確認済み'], ['conflicting', '矛盾あり']], row.verificationStatus || 'candidate')}</select></label>
            <label>根拠ID<input name="evidenceId" value="${escapeHtml(row.evidenceId || '')}" placeholder="EV-0000000000 / 未発行可"></label>
            <label class="wide">メモ<textarea name="notes">${escapeHtml(row.notes || '')}</textarea></label>
          </div>
        </section>

        <p id="editMessage" class="message">DRAFT保存、または保存してv0.4受信箱へ送信してください。</p>
        <div class="sticky"><button type="button" class="secondary" id="back">一覧へ戻る</button><button type="submit" class="secondary" id="saveDraft">${editing ? 'UPDATEをDRAFT保存' : 'DRAFT保存'}</button><button type="button" id="saveAndSend">保存してv0.4受信箱へ送る</button></div>
      </form>
    </div>`;

    const form = document.getElementById('capture');
    form.priority.value = row.priority || 'NORMAL';
    form.targetType.value = row.targetType || 'yarn';

    for (const [type, label] of PHOTO_TYPES) {
      const reference = (row.photoRefs || []).find((item) => item.type === type);
      if (reference) {
        const photo = await getOne('photos', reference.photoId);
        if (photo?.blob) {
          const url = URL.createObjectURL(photo.blob);
          editor.querySelector(`[data-preview="${type}"]`).innerHTML = `<img src="${url}" alt="${escapeHtml(label)}"><figcaption>保存済み / ${escapeHtml(reference.fileName || label)}</figcaption>`;
        }
      }
    }

    editor.querySelectorAll('[data-input]').forEach((input) => {
      input.addEventListener('change', () => {
        const file = input.files[0];
        if (!file) return;
        pendingPhotos[input.dataset.input] = file;
        const url = URL.createObjectURL(file);
        editor.querySelector(`[data-preview="${input.dataset.input}"]`).innerHTML = `<img src="${url}" alt="新規写真"><figcaption>新規選択 / ${escapeHtml(file.name)}</figcaption>`;
      });
    });

    form.compositionRaw.addEventListener('input', () => renderCompositionTotal(form.compositionRaw.value));
    renderCompositionTotal(form.compositionRaw.value);
    document.getElementById('back').addEventListener('click', () => {
      editor.classList.add('hidden');
      document.getElementById('inbox').scrollIntoView();
    });
    document.getElementById('saveDraft').addEventListener('click', () => {
      submitMode = 'draft';
    });
    document.getElementById('saveAndSend').addEventListener('click', () => {
      submitMode = 'send';
      form.requestSubmit();
    });
    form.addEventListener('invalid', () => {
      submitMode = 'draft';
    }, true);
    form.addEventListener('submit', saveCapture);
    editor.scrollIntoView({ behavior: 'smooth' });
  }

  function parseComposition(text) {
    const values = [...String(text || '').matchAll(/(\d+(?:\.\d+)?)\s*%/g)].map((match) => Number(match[1]));
    const total = values.reduce((sum, value) => sum + value, 0);
    return { values, total };
  }

  function renderCompositionTotal(text) {
    const totalElement = document.getElementById('compositionTotal');
    const messageElement = document.getElementById('compositionMessage');
    if (!totalElement || !messageElement) return;
    const result = parseComposition(text);
    if (!result.values.length) {
      totalElement.textContent = '—';
      totalElement.className = '';
      messageElement.textContent = /\d/.test(String(text || '')) ? '合計確認する数値には%を付けてください。' : '数値を入力すると合計を確認します。';
      return;
    }
    totalElement.textContent = `${result.total}%`;
    totalElement.className = Math.abs(result.total - 100) < 0.01 ? 'ok' : 'warn';
    messageElement.textContent = Math.abs(result.total - 100) < 0.01 ? '合計100%です。' : '合計100%ではありません。Human Reviewで確認してください。';
  }

  function checkedValues(form, name) {
    return [...form.querySelectorAll(`[name="${name}"]:checked`)].map((input) => input.value);
  }

  function propertyItems(codes, options, status, detail, extra = {}) {
    const labels = new Map(options);
    return codes.map((code) => ({ code, name: labels.get(code) || code, verification_status: status, detail, ...extra }));
  }

  function normalizeCommonIds(targetType, targetId, form) {
    const ids = {
      productId: form.productId.value.trim(),
      yarnId: form.yarnId.value.trim(),
      materialId: form.materialId.value.trim(),
      researchId: form.researchId.value.trim()
    };
    if (targetType === 'product') ids.productId = targetId;
    if (targetType === 'yarn') ids.yarnId = targetId;
    if (targetType === 'material') ids.materialId = targetId;
    if (targetType === 'research') ids.researchId = targetId;
    return ids;
  }

  async function saveCapture(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const targetType = form.targetType.value;
    const targetId = form.targetId.value.trim() || editing?.snapshot?.targetId || temporaryCommonId(targetType);
    const recordId = editing?.recordId || internalId('KCI-CAPTURE');
    const existingPhotoRefs = [...(editing?.snapshot.photoRefs || [])];
    const newPhotoRefs = [];
    const photoRows = [];

    for (const [type, label] of PHOTO_TYPES) {
      const file = pendingPhotos[type];
      if (!file) continue;
      const photoId = `TMP-PH-${uuid()}`;
      const capturedAt = nowIso();
      newPhotoRefs.push({ photoId, type, label, fileName: file.name, capturedAt });
      photoRows.push({ photoId, recordId, targetId, type, label, fileName: file.name, blob: file, capturedAt });
    }
    const replacedTypes = new Set(newPhotoRefs.map((reference) => reference.type));
    const photoRefs = [...existingPhotoRefs.filter((reference) => !replacedTypes.has(reference.type)), ...newPhotoRefs];

    const composition = parseComposition(form.compositionRaw.value);
    const functionCodes = checkedValues(form, 'functionCodes');
    const sustainableCodes = checkedValues(form, 'sustainableCodes');
    const captureId = editing?.snapshot?.captureId || recordId;
    const snapshot = {
      dataContractVersion: DATA_CONTRACT_VERSION,
      captureId,
      priority: form.priority.value,
      targetType,
      targetId,
      commonIds: normalizeCommonIds(targetType, targetId, form),
      sourceOrganizationName: form.sourceOrganizationName.value.trim(),
      sourceOrganizationId: form.sourceOrganizationId.value.trim(),
      manufacturerName: form.manufacturerName.value.trim(),
      manufacturerId: form.manufacturerId.value.trim(),
      sellerName: form.sellerName.value.trim(),
      sellerId: form.sellerId.value.trim(),
      brandName: form.brandName.value.trim(),
      productName: form.productName.value.trim(),
      productCode: form.productCode.value.trim(),
      productUrl: form.productUrl.value.trim(),
      yarnName: form.yarnName.value.trim(),
      yarnCode: form.yarnCode.value.trim(),
      countSystem: form.countSystem.value,
      countValue: form.countValue.value.trim(),
      countDisplay: form.countDisplay.value.trim(),
      gauge: form.gauge.value.trim(),
      basicYarnForm: form.basicYarnForm.value,
      yarnStructure: form.yarnStructure.value.trim(),
      spinningMethod: form.spinningMethod.value,
      processingMethod: form.processingMethod.value.trim(),
      compositionRaw: form.compositionRaw.value.trim(),
      compositionTotal: composition.values.length ? composition.total : null,
      compositionStatus: form.compositionStatus.value,
      functionalProperties: propertyItems(functionCodes, FUNCTION_OPTIONS, form.functionClaimStatus.value, form.functionDetail.value.trim(), { test: form.functionTest.value.trim() }),
      functionClaimStatus: form.functionClaimStatus.value,
      functionDetail: form.functionDetail.value.trim(),
      functionTest: form.functionTest.value.trim(),
      sustainableAttributes: propertyItems(sustainableCodes, SUSTAINABLE_OPTIONS, form.sustainableStatus.value, form.sustainableBasis.value.trim(), { certification: form.certification.value.trim() }),
      sustainableStatus: form.sustainableStatus.value,
      sustainableBasis: form.sustainableBasis.value.trim(),
      certification: form.certification.value.trim(),
      seasons: checkedValues(form, 'season'),
      documentType: form.documentType.value,
      sourceType: form.sourceType.value,
      sourceUrl: form.sourceUrl.value.trim(),
      verificationStatus: form.verificationStatus.value,
      evidenceId: form.evidenceId.value.trim(),
      notes: form.notes.value.trim(),
      photoRefs
    };

    const meaningful = photoRefs.length || snapshot.yarnName || snapshot.productName || snapshot.organizationName
      || snapshot.sourceOrganizationName || snapshot.compositionRaw || snapshot.notes;
    if (!meaningful) {
      document.getElementById('editMessage').textContent = '写真または対象情報を入力してください。';
      submitMode = 'draft';
      return;
    }

    const timestamp = nowIso();
    const eventRow = {
      eventId: internalId('KCI-EVENT'),
      recordId,
      version: editing ? Number(editing.version) + 1 : 1,
      eventType: editing ? 'UPDATE' : 'CREATE',
      dataState: 'DRAFT',
      createdAt: editing?.createdAt || timestamp,
      updatedAt: timestamp,
      actorId: session.accountId,
      snapshot
    };

    const transaction = db.transaction(['events', 'photos'], 'readwrite');
    transaction.objectStore('events').add(eventRow);
    photoRows.forEach((row) => transaction.objectStore('photos').add(row));
    await transactionPromise(transaction);

    let handoffError = null;
    if (submitMode === 'send') {
      try {
        enqueueHandoff(eventRow);
      } catch (error) {
        handoffError = error;
      }
    }
    submitMode = 'draft';
    editing = null;
    await renderApp();
    document.getElementById('inbox').scrollIntoView({ behavior: 'smooth' });
    if (handoffError) {
      alert(`DRAFTは保存しましたが、v0.4受信箱へ送信できませんでした。一覧から再送してください。\n\n${handoffError.message || handoffError}`);
    }
  }

  function sanitizeForHandoff(snapshot) {
    return {
      ...snapshot,
      photoRefs: (snapshot.photoRefs || []).map(({ photoId, type, label, fileName, capturedAt }) => ({ photoId, type, label, fileName, capturedAt }))
    };
  }

  function enqueueHandoff(eventRow) {
    const queue = handoffQueue();
    const dedupeKey = `${eventRow.recordId}:${eventRow.version}`;
    if (queue.some((item) => item.dedupe_key === dedupeKey)) return;
    queue.unshift({
      format: 'KC_V04_INBOX_ITEM',
      schema_version: '1.0',
      handoff_id: internalId('HF'),
      dedupe_key: dedupeKey,
      capture_id: eventRow.snapshot.captureId || eventRow.recordId,
      event_id: eventRow.eventId,
      event_version: eventRow.version,
      source_system: 'KC-PHOTO-CAPTURE',
      sent_at: nowIso(),
      review_status: 'PENDING',
      payload: sanitizeForHandoff(eventRow.snapshot)
    });
    saveHandoffQueue(queue);
  }

  async function enqueueExisting(recordId) {
    const row = records.find((event) => event.recordId === recordId);
    if (!row) return;
    enqueueHandoff(row);
    await renderApp();
  }

  function exportHandoffQueue() {
    const queue = handoffQueue();
    if (!queue.length) {
      alert('受信箱へ送ったデータがありません。');
      return;
    }
    const envelope = {
      format: 'KC_V04_INBOX_EXPORT',
      schema_version: '1.0',
      exported_at: nowIso(),
      source_system: 'KC-PHOTO-CAPTURE',
      items: queue
    };
    const blob = new Blob([JSON.stringify(envelope, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `KC_v04_inbox_${new Date().toISOString().slice(0, 10)}.json`;
    anchor.rel = 'noopener';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  openDatabase().catch((error) => shell(`<section class="card"><h1>Sandboxを開始できません</h1><p class="message error">${escapeHtml(error.message)}</p></section>`));
})();
