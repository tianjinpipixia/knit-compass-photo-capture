(() => {
  'use strict';

  const root = document.getElementById('app');
  if (!root) return;

  const DB_NAME = 'kc_independent_photo_capture_v1_0';
  const SESSION_KEY = 'kc_session_v1';
  const AUTH_REALM = 'KNIT_COMPASS_DEVICE_LOCAL';

  function isExistingLogin(form) {
    const submit = form?.querySelector('button[type="submit"]');
    return String(submit?.textContent || '').trim() === '保存データを開く';
  }

  function setMessage(text, isError = false) {
    const message = document.getElementById('kcAuthMessage');
    if (!message) return;
    message.textContent = text;
    message.classList.toggle('error', isError);
  }

  function focusPassphrase(pass) {
    if (!(pass instanceof HTMLInputElement)) return;
    pass.disabled = false;
    pass.readOnly = false;
    pass.removeAttribute('readonly');
    pass.removeAttribute('disabled');
    pass.setAttribute('inputmode', 'text');
    pass.setAttribute('enterkeyhint', 'go');
    pass.style.pointerEvents = 'auto';
    pass.focus({ preventScroll: false });
    try {
      const end = pass.value.length;
      pass.setSelectionRange(end, end);
    } catch (_error) {
      // Password fields may reject selection APIs on some Android builds.
    }
  }

  function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME);
      request.addEventListener('success', () => resolve(request.result), { once: true });
      request.addEventListener('error', () => reject(request.error || new Error('端末内データベースを開けません')), { once: true });
      request.addEventListener('blocked', () => reject(new Error('別のPhoto Capture画面を閉じてください')), { once: true });
    });
  }

  function readAccounts(db) {
    return new Promise((resolve, reject) => {
      if (!db.objectStoreNames.contains('accounts')) {
        reject(new Error('保存済み利用者が見つかりません'));
        return;
      }
      const tx = db.transaction('accounts', 'readonly');
      const request = tx.objectStore('accounts').getAll();
      request.addEventListener('success', () => resolve(Array.isArray(request.result) ? request.result : []), { once: true });
      request.addEventListener('error', () => reject(request.error || new Error('保存済み利用者を確認できません')), { once: true });
    });
  }

  async function unlockOnThisDevice(button) {
    if (button) button.disabled = true;
    setMessage('この端末の保存データを確認しています…');
    let db;
    try {
      db = await openDatabase();
      const accounts = await readAccounts(db);
      if (accounts.length !== 1 || !accounts[0]?.accountId) {
        throw new Error(accounts.length > 1 ? '利用者が複数あるためパスフレーズで開いてください' : '保存済み利用者が見つかりません');
      }
      const account = accounts[0];
      sessionStorage.setItem(SESSION_KEY, JSON.stringify({
        accountId: account.accountId,
        displayName: account.displayName || 'Knit Compass Owner',
        realm: AUTH_REALM
      }));
      setMessage('端末認証を確認しました。保存データを開きます…');
      location.reload();
    } catch (error) {
      setMessage(`端末認証で開けませんでした: ${error.message || error}`, true);
      if (button) button.disabled = false;
    } finally {
      try { db?.close(); } catch (_error) {}
    }
  }

  function ensureDeviceUnlockButton(form) {
    let button = form.querySelector('[data-kc-device-unlock]');
    if (button) return button;
    button = document.createElement('button');
    button.type = 'button';
    button.className = 'secondary';
    button.dataset.kcDeviceUnlock = '1';
    button.textContent = 'この端末の保存データを開く';
    button.addEventListener('click', () => void unlockOnThisDevice(button));
    form.appendChild(button);
    return button;
  }

  function ensureDirectInputButton(form, pass) {
    let button = form.querySelector('[data-kc-pass-focus]');
    if (button) return button;
    button = document.createElement('button');
    button.type = 'button';
    button.className = 'secondary';
    button.dataset.kcPassFocus = '1';
    button.textContent = 'パスフレーズを直接入力';
    button.addEventListener('click', () => {
      pass.type = 'text';
      pass.style.webkitTextSecurity = 'disc';
      pass.autocomplete = 'off';
      focusPassphrase(pass);
      setMessage('パスフレーズ欄を直接入力モードにしました。');
    });
    const submit = form.querySelector('button[type="submit"]');
    if (submit) submit.insertAdjacentElement('beforebegin', button);
    else form.appendChild(button);
    return button;
  }

  function patchAuthForm() {
    const form = document.getElementById('auth');
    if (!form) return;

    const pass = form.elements?.pass;
    if (!(pass instanceof HTMLInputElement)) return;

    if (isExistingLogin(form)) {
      form.noValidate = true;
      pass.removeAttribute('minlength');
      pass.autocomplete = 'current-password';
      pass.disabled = false;
      pass.readOnly = false;
      pass.setAttribute('inputmode', 'text');
      pass.setAttribute('enterkeyhint', 'go');
      pass.style.pointerEvents = 'auto';
      const help = pass.closest('label')?.querySelector('small');
      if (help) help.textContent = '保存済みのパスフレーズを入力してください。入力できない場合は下の端末認証を使えます。';

      ensureDirectInputButton(form, pass);
      ensureDeviceUnlockButton(form);

      if (!form.dataset.kcLegacyLoginFeedback) {
        form.dataset.kcLegacyLoginFeedback = '1';
        form.addEventListener('submit', () => {
          setMessage('保存データを確認しています…');
        }, true);
        pass.addEventListener('pointerdown', () => focusPassphrase(pass), true);
        pass.addEventListener('input', () => {
          if (pass.value) setMessage('パスフレーズを入力しました。「保存データを開く」を押してください。');
        });
        pass.addEventListener('change', () => {
          if (pass.value) setMessage('保存済みパスフレーズを受け取りました。');
        });
      }
    } else {
      form.noValidate = false;
      pass.minLength = 10;
      pass.autocomplete = 'new-password';
    }
  }

  root.addEventListener('click', (event) => {
    const button = event.target.closest?.('#auth button[type="submit"]');
    if (button) patchAuthForm();
  }, true);

  const observer = new MutationObserver(patchAuthForm);
  observer.observe(root, { childList: true, subtree: true });
  patchAuthForm();
})();
