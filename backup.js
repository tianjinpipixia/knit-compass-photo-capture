(() => {
  'use strict';

  const DB_NAME = 'kc_independent_photo_capture_v1_0';
  const BACKUP_FORMAT = 'KC_PHOTO_CAPTURE_BACKUP';
  const BACKUP_VERSION = 1;
  const FEATURE_VERSION = '1.0.0';
  const MAX_BACKUP_BYTES = 350 * 1024 * 1024;
  const LAST_BACKUP_KEY = 'kc_photo_capture_last_backup_v1';
  const STORES = ['accounts', 'events', 'photos'];
  const KEY_PATHS = { accounts: 'accountId', events: 'eventId', photos: 'photoId' };
  const root = document.getElementById('app');
  let dbPromise;

  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[character]);

  function formatDate(value) {
    return value
      ? new Intl.DateTimeFormat('ja-JP', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
      : 'まだ書き出していません';
  }

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

  function openDatabase() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
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
    return dbPromise;
  }

  async function getAll(storeName) {
    const database = await openDatabase();
    const transaction = database.transaction(storeName, 'readonly');
    const rows = await requestPromise(transaction.objectStore(storeName).getAll());
    await transactionPromise(transaction);
    return rows;
  }

  function setMessage(id, text, isError = false) {
    const element = document.getElementById(id);
    if (!element) return;
    element.textContent = text;
    element.classList.toggle('error', isError);
  }

  function canonicalize(value) {
    if (Array.isArray(value)) return value.map(canonicalize);
    if (value && typeof value === 'object' && Object.getPrototypeOf(value) === Object.prototype) {
      return Object.keys(value).sort().reduce((result, key) => {
        result[key] = canonicalize(value[key]);
        return result;
      }, {});
    }
    return value;
  }

  async function sha256Text(text) {
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  }

  async function sha256Blob(blob) {
    const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer());
    return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('');
  }

  function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const result = String(reader.result || '');
        const comma = result.indexOf(',');
        resolve(comma >= 0 ? result.slice(comma + 1) : result);
      };
      reader.onerror = () => reject(reader.error || new Error('PHOTO_ENCODING_FAILED'));
      reader.readAsDataURL(blob);
    });
  }

  function base64ToBlob(base64, mediaType = 'application/octet-stream') {
    const binary = atob(base64);
    const chunks = [];
    const chunkSize = 1024 * 1024;
    for (let offset = 0; offset < binary.length; offset += chunkSize) {
      const slice = binary.slice(offset, offset + chunkSize);
      const bytes = new Uint8Array(slice.length);
      for (let index = 0; index < slice.length; index += 1) bytes[index] = slice.charCodeAt(index);
      chunks.push(bytes);
    }
    return new Blob(chunks, { type: mediaType });
  }

  function backupFileName(exportedAt) {
    const stamp = exportedAt.replace(/[-:]/g, '').replace('T', '-').replace(/\..+$/, '');
    return `KC_PhotoCapture_Backup_${stamp}.kcbackup.json`;
  }

  function triggerDownload(file) {
    const url = URL.createObjectURL(file);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = file.name;
    anchor.rel = 'noopener';
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  async function saveOrShare(file) {
    if (navigator.share && navigator.canShare?.({ files: [file] })) {
      try {
        await navigator.share({
          title: 'Knit Compass Photo Capture Backup',
          text: 'Knit Compass Photo Captureのバックアップです。Google Driveなど本人専用の場所へ保存してください。',
          files: [file]
        });
        return { saved: true, message: '共有先への書き出しを完了しました。Google Driveなどに保存されたことを確認してください。' };
      } catch (error) {
        if (error?.name === 'AbortError') {
          return { saved: false, message: '書き出しをキャンセルしました。データは変更されていません。' };
        }
      }
    }
    triggerDownload(file);
    return { saved: true, message: 'バックアップをダウンロードしました。Downloadsまたは選択した保存先を確認してください。' };
  }

  async function exportBackup() {
    const button = document.getElementById('kcExportBackup');
    if (!button) return;
    button.disabled = true;
    setMessage('kcBackupMessage', 'バックアップを作成しています。画面を閉じないでください。');

    try {
      const [accounts, events, photoRows] = await Promise.all(STORES.map((store) => getAll(store)));
      const photos = [];

      for (let index = 0; index < photoRows.length; index += 1) {
        const photo = photoRows[index];
        setMessage('kcBackupMessage', `写真をバックアップへ格納しています（${index + 1}/${photoRows.length}）。`);
        const { blob, ...metadata } = photo;
        if (!(blob instanceof Blob)) throw new Error(`写真データを読み取れません: ${photo.photoId}`);
        photos.push({
          ...metadata,
          mediaType: blob.type || metadata.mediaType || 'application/octet-stream',
          size: blob.size,
          sha256: await sha256Blob(blob),
          dataBase64: await blobToBase64(blob)
        });
      }

      const exportedAt = new Date().toISOString();
      const payload = {
        manifest: {
          application: 'Knit Compass Photo Capture',
          backupFeatureVersion: FEATURE_VERSION,
          backupVersion: BACKUP_VERSION,
          databaseName: DB_NAME,
          exportedAt,
          historyPolicy: 'APPEND_ONLY',
          automaticSync: 'OFF',
          counts: { accounts: accounts.length, events: events.length, photos: photos.length }
        },
        accounts,
        events,
        photos
      };

      const checksum = await sha256Text(JSON.stringify(canonicalize(payload)));
      const envelope = {
        format: BACKUP_FORMAT,
        backupVersion: BACKUP_VERSION,
        checksum: { algorithm: 'SHA-256', value: checksum },
        payload
      };
      const file = new File(
        [JSON.stringify(envelope, null, 2)],
        backupFileName(exportedAt),
        { type: 'application/json' }
      );
      const result = await saveOrShare(file);
      if (result.saved) {
        localStorage.setItem(LAST_BACKUP_KEY, exportedAt);
        const lastBackup = document.getElementById('kcLastBackup');
        if (lastBackup) lastBackup.textContent = formatDate(exportedAt);
      }
      setMessage('kcBackupMessage', `${result.message} アカウント${accounts.length}件・履歴${events.length}件・写真${photos.length}件。`);
    } catch (error) {
      setMessage('kcBackupMessage', `バックアップを作成できませんでした: ${error.message || error}`, true);
    } finally {
      if (document.contains(button)) button.disabled = false;
    }
  }

  function validateUniqueKeys(rows, keyPath, label) {
    const seen = new Set();
    for (const row of rows) {
      const key = row?.[keyPath];
      if (!key || typeof key !== 'string') throw new Error(`${label}に有効なIDがありません`);
      if (seen.has(key)) throw new Error(`${label}に重複IDがあります: ${key}`);
      seen.add(key);
    }
  }

  async function decodeBackup(file) {
    if (!file) throw new Error('バックアップファイルを選択してください');
    if (file.size > MAX_BACKUP_BYTES) throw new Error('バックアップファイルが大きすぎます（上限350MB）');

    let envelope;
    try {
      envelope = JSON.parse(await file.text());
    } catch {
      throw new Error('JSON形式のバックアップとして読み取れません');
    }

    if (envelope?.format !== BACKUP_FORMAT || envelope?.backupVersion !== BACKUP_VERSION) {
      throw new Error('Knit Compass Photo Captureの対応バックアップではありません');
    }
    if (envelope?.checksum?.algorithm !== 'SHA-256' || !envelope?.checksum?.value) {
      throw new Error('バックアップの検証情報がありません');
    }

    const payload = envelope.payload;
    if (!payload || !Array.isArray(payload.accounts) || !Array.isArray(payload.events) || !Array.isArray(payload.photos)) {
      throw new Error('バックアップのデータ構造が不正です');
    }

    const checksum = await sha256Text(JSON.stringify(canonicalize(payload)));
    if (checksum !== envelope.checksum.value) {
      throw new Error('バックアップが破損または変更されています（SHA-256不一致）');
    }

    const counts = payload.manifest?.counts;
    if (!counts
      || counts.accounts !== payload.accounts.length
      || counts.events !== payload.events.length
      || counts.photos !== payload.photos.length) {
      throw new Error('バックアップ件数が一致しません');
    }

    validateUniqueKeys(payload.accounts, 'accountId', 'アカウント');
    validateUniqueKeys(payload.events, 'eventId', '履歴');
    validateUniqueKeys(payload.photos, 'photoId', '写真');

    const photos = [];
    for (let index = 0; index < payload.photos.length; index += 1) {
      const encoded = payload.photos[index];
      if (typeof encoded.dataBase64 !== 'string' || !encoded.dataBase64) {
        throw new Error(`写真データがありません: ${encoded.photoId}`);
      }
      const { dataBase64, sha256, ...metadata } = encoded;
      let blob;
      try {
        blob = base64ToBlob(dataBase64, metadata.mediaType || 'application/octet-stream');
      } catch {
        throw new Error(`写真データを復号できません: ${metadata.photoId}`);
      }
      if (metadata.size !== blob.size) throw new Error(`写真サイズが一致しません: ${metadata.photoId}`);
      if (sha256 && await sha256Blob(blob) !== sha256) throw new Error(`写真が破損しています: ${metadata.photoId}`);
      photos.push({ ...metadata, blob });
    }

    return { manifest: payload.manifest, accounts: payload.accounts, events: payload.events, photos };
  }

  function normalizePhoto(row) {
    if (!row) return row;
    const { blob, mediaType, size, ...rest } = row;
    return {
      ...rest,
      mediaType: blob?.type || mediaType || 'application/octet-stream',
      size: blob?.size ?? size ?? 0
    };
  }

  async function rowsEqual(storeName, existing, incoming) {
    if (storeName !== 'photos') {
      return JSON.stringify(canonicalize(existing)) === JSON.stringify(canonicalize(incoming));
    }
    const metadataEqual = JSON.stringify(canonicalize(normalizePhoto(existing)))
      === JSON.stringify(canonicalize(normalizePhoto(incoming)));
    if (!metadataEqual) return false;
    if (!(existing.blob instanceof Blob) || !(incoming.blob instanceof Blob)) return false;
    return await sha256Blob(existing.blob) === await sha256Blob(incoming.blob);
  }

  async function determineRowsToAdd(storeName, incomingRows) {
    const keyPath = KEY_PATHS[storeName];
    const existingRows = await getAll(storeName);
    const existingMap = new Map(existingRows.map((row) => [row[keyPath], row]));
    const rowsToAdd = [];

    for (const incoming of incomingRows) {
      const key = incoming[keyPath];
      const existing = existingMap.get(key);
      if (!existing) {
        rowsToAdd.push(incoming);
      } else if (!await rowsEqual(storeName, existing, incoming)) {
        throw new Error(`${storeName}の同一IDに異なるデータがあります: ${key}`);
      }
    }
    return rowsToAdd;
  }

  async function restoreBackup(file, messageId) {
    setMessage(messageId, 'バックアップを検証しています。画面を閉じないでください。');
    const backup = await decodeBackup(file);
    const counts = backup.manifest.counts;
    const approved = window.confirm(
      `バックアップを安全に統合します。\n\nアカウント: ${counts.accounts}件\n履歴: ${counts.events}件\n写真: ${counts.photos}件\n\n現在のデータは削除しません。続行しますか？`
    );
    if (!approved) {
      setMessage(messageId, '復元をキャンセルしました。データは変更されていません。');
      return;
    }

    setMessage(messageId, '既存データとの重複・競合を確認しています。');
    const [accountsToAdd, eventsToAdd, photosToAdd] = await Promise.all([
      determineRowsToAdd('accounts', backup.accounts),
      determineRowsToAdd('events', backup.events),
      determineRowsToAdd('photos', backup.photos)
    ]);

    const database = await openDatabase();
    const transaction = database.transaction(STORES, 'readwrite');
    accountsToAdd.forEach((row) => transaction.objectStore('accounts').add(row));
    eventsToAdd.forEach((row) => transaction.objectStore('events').add(row));
    photosToAdd.forEach((row) => transaction.objectStore('photos').add(row));
    await transactionPromise(transaction);

    const summary = `復元完了：アカウント${accountsToAdd.length}件・履歴${eventsToAdd.length}件・写真${photosToAdd.length}件を追加しました。重複データは安全にスキップしました。`;
    window.alert(`${summary}\n\n画面を再読み込みします。`);
    window.location.reload();
  }

  function wireRestore(buttonId, inputId, messageId) {
    const button = document.getElementById(buttonId);
    const input = document.getElementById(inputId);
    if (!button || !input) return;
    button.onclick = () => input.click();
    input.onchange = async () => {
      const file = input.files?.[0];
      input.value = '';
      if (!file) return;
      button.disabled = true;
      try {
        await restoreBackup(file, messageId);
      } catch (error) {
        setMessage(messageId, `復元できませんでした: ${error.message || error}`, true);
      } finally {
        if (document.contains(button)) button.disabled = false;
      }
    };
  }

  function backupCardTemplate() {
    return `
      <section class="card protection-card" id="kcBackupCard">
        <p class="eyebrow">Data Protection / Backup ${FEATURE_VERSION}</p>
        <h2>バックアップ・復元</h2>
        <p class="lead">端末内のアカウント、登録情報、CREATE／UPDATE履歴、写真を1つのファイルにまとめます。</p>
        <div class="protection-summary">
          <div><span>保存場所</span><strong>この端末内</strong></div>
          <div><span>最終書き出し</span><strong id="kcLastBackup">${escapeHtml(formatDate(localStorage.getItem(LAST_BACKUP_KEY)))}</strong></div>
        </div>
        <div class="protection-actions">
          <button type="button" id="kcExportBackup">バックアップを書き出す</button>
          <button type="button" class="secondary" id="kcRestoreBackup">バックアップから復元</button>
        </div>
        <input class="visually-hidden" id="kcRestoreBackupInput" type="file" accept=".json,.kcbackup,application/json">
        <p id="kcBackupMessage" class="message">ファイルには写真と素材情報が含まれます。Androidでは保存先にGoogle Driveなど本人専用の場所を選んでください。</p>
      </section>`;
  }

  function authRestoreCardTemplate() {
    return `
      <section class="card protection-card" id="kcAuthRestoreCard">
        <p class="eyebrow">Restore Access</p>
        <h2>バックアップから復元</h2>
        <p class="lead">機種変更時は、以前に書き出したバックアップを選択してください。既存データは削除せず、安全に統合します。</p>
        <button type="button" class="secondary" id="kcAuthRestore">バックアップファイルを選択</button>
        <input class="visually-hidden" id="kcAuthRestoreInput" type="file" accept=".json,.kcbackup,application/json">
        <p id="kcAuthRestoreMessage" class="message">復元後は、バックアップ作成時のAccount IDとパスフレーズでログインします。</p>
      </section>`;
  }

  function injectControls() {
    const inbox = document.getElementById('inbox');
    if (inbox && !document.getElementById('kcBackupCard')) {
      inbox.insertAdjacentHTML('beforebegin', backupCardTemplate());
      document.getElementById('kcExportBackup').onclick = exportBackup;
      wireRestore('kcRestoreBackup', 'kcRestoreBackupInput', 'kcBackupMessage');
    }

    const authForm = document.getElementById('auth');
    const main = root?.querySelector('main.app');
    if (authForm && main && !document.getElementById('kcAuthRestoreCard')) {
      main.insertAdjacentHTML('beforeend', authRestoreCardTemplate());
      wireRestore('kcAuthRestore', 'kcAuthRestoreInput', 'kcAuthRestoreMessage');
    }
  }

  const observer = new MutationObserver(() => queueMicrotask(injectControls));
  if (root) observer.observe(root, { childList: true, subtree: true });
  injectControls();
})();