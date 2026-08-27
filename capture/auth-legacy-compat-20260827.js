(() => {
  'use strict';

  const root = document.getElementById('app');
  if (!root) return;

  function isExistingLogin(form) {
    const submit = form?.querySelector('button[type="submit"]');
    return String(submit?.textContent || '').trim() === '保存データを開く';
  }

  function patchAuthForm() {
    const form = document.getElementById('auth');
    if (!form) return;

    const pass = form.elements?.pass;
    if (!(pass instanceof HTMLInputElement)) return;

    if (isExistingLogin(form)) {
      // Older device-local accounts may have been created before the current
      // 10-character creation rule existed. Do not block those accounts with
      // native minlength validation before the app can verify the saved hash.
      form.noValidate = true;
      pass.removeAttribute('minlength');
      pass.autocomplete = 'current-password';
      const help = pass.closest('label')?.querySelector('small');
      if (help) help.textContent = '保存済みのパスフレーズを入力してください。';

      if (!form.dataset.kcLegacyLoginFeedback) {
        form.dataset.kcLegacyLoginFeedback = '1';
        form.addEventListener('submit', () => {
          const message = document.getElementById('kcAuthMessage');
          if (message) {
            message.textContent = '保存データを確認しています…';
            message.classList.remove('error');
          }
        }, true);
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
