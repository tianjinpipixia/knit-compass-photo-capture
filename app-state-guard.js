(() => {
  'use strict';

  const FORM_ID = 'capture';
  const HANDOFF_KEY = 'kc_v04_handoff_queue_v1';
  const EDITOR_DRAFT_KEY = 'kc_photo_capture_editor_draft_v1';
  const DRAFT_SAVE_DELAY_MS = 250;
  const DRAFT_STATUS_LABELS = new Set(['端末に下書き保存', '下書き保存']);
  const REVIEW_ACTION_LABELS = new Set(['受信箱で内容確認', 'Human Review受信箱を開く']);
  const FORMAL_STATUS_LABELS = new Set(['正式登録は人が確認', '確認後に正式登録']);

  let activeForm = null;
  let draftTimer = null;

  function handoffQueue() {
    try {
      const parsed = JSON.parse(localStorage.getItem(HANDOFF_KEY) || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  function recordVersion(card) {
    const text = [...card.querySelectorAll('.meta span')]
      .map((element) => element.textContent || '')
      .join(' ');
    return Number(text.match(/\bv(\d+)\b/)?.[1] || 0);
  }

  function handoffForVersion(recordId, version) {
    if (!recordId || !version) return null;
    const dedupeKey = `${recordId}:${version}`;
    return handoffQueue().find((item) => item?.dedupe_key === dedupeKey) || null;
  }

  function handoffLabel(item) {
    if (!item) return 'Human Review受信箱へ送る';
    if (item.review_status === 'APPROVED') return '承認済み';
    if (item.review_status === 'REJECTED') return '差戻し済み（編集して再送）';
    return '受信箱へ送信済み';
  }

  function refreshRecordSendState(root = document) {
    root.querySelectorAll('[data-send]').forEach((button) => {
      const card = button.closest('.record');
      if (!card) return;
      const version = recordVersion(card);
      const item = handoffForVersion(button.dataset.send, version);
      const sent = Boolean(item);
      button.disabled = sent;
      button.setAttribute('aria-disabled', sent ? 'true' : 'false');
      button.removeAttribute('aria-busy');
      const label = handoffLabel(item);
      if (button.textContent !== label) button.textContent = label;

      const status = [...card.querySelectorAll('.meta span')]
        .find((element) => (element.textContent || '').startsWith('受信箱:'));
      if (status) {
        const label = `受信箱: ${item?.review_status || '未送信'}`;
        if (status.textContent !== label) status.textContent = label;
      }
    });
  }

  function formMessage(form) {
    return form.querySelector('#editMessage');
  }

  function setFormMessage(form, text, isError = false) {
    const message = formMessage(form);
    if (!message) return;
    message.textContent = text;
    message.classList.toggle('error', isError);
  }

  function setFormBusy(form, busy) {
    form.dataset.saveInFlight = busy ? 'true' : 'false';
    form.setAttribute('aria-busy', busy ? 'true' : 'false');
    for (const id of ['back', 'saveDraft', 'saveAndSend']) {
      const button = form.querySelector(`#${id}`);
      if (!button) continue;
      button.disabled = busy;
      button.setAttribute('aria-disabled', busy ? 'true' : 'false');
    }
  }

  function serializableFormValues(form) {
    const values = {};
    for (const field of form.elements) {
      if (!field.name || field.type === 'file' || field.type === 'button' || field.type === 'submit') continue;
      if (field.type === 'checkbox' || field.type === 'radio') {
        if (!Array.isArray(values[field.name])) values[field.name] = [];
        if (field.checked) values[field.name].push(field.value);
      } else {
        values[field.name] = field.value;
      }
    }
    return values;
  }

  function fingerprint(value) {
    const text = JSON.stringify(value);
    let hash = 2166136261;
    for (let index = 0; index < text.length; index += 1) {
      hash ^= text.charCodeAt(index);
      hash = Math.imul(hash, 16777619);
    }
    return (hash >>> 0).toString(16);
  }

  function readEditorDraft() {
    try {
      const parsed = JSON.parse(sessionStorage.getItem(EDITOR_DRAFT_KEY) || 'null');
      return parsed && typeof parsed === 'object' ? parsed : null;
    } catch {
      return null;
    }
  }

  function writeEditorDraft(form) {
    if (!form?.isConnected || form.dataset.saveInFlight === 'true') return;
    const draft = {
      fingerprint: form.dataset.initialFingerprint,
      values: serializableFormValues(form),
      hasPendingFiles: form.dataset.hasPendingFiles === 'true',
      savedAt: new Date().toISOString()
    };
    try {
      sessionStorage.setItem(EDITOR_DRAFT_KEY, JSON.stringify(draft));
    } catch {
      setFormMessage(form, '入力途中データを一時保存できません。DRAFT保存を実行してください。', true);
    }
  }

  function scheduleEditorDraft(form) {
    clearTimeout(draftTimer);
    draftTimer = window.setTimeout(() => writeEditorDraft(form), DRAFT_SAVE_DELAY_MS);
  }

  function applyEditorDraft(form, draft) {
    for (const field of form.elements) {
      if (!field.name || !(field.name in draft.values) || field.type === 'file') continue;
      const stored = draft.values[field.name];
      if (field.type === 'checkbox' || field.type === 'radio') {
        field.checked = Array.isArray(stored) && stored.includes(field.value);
      } else if (typeof stored === 'string') {
        field.value = stored;
      }
    }
    setFormMessage(
      form,
      draft.hasPendingFiles
        ? '入力途中の内容を復元しました。未保存の写真だけ再選択してください。'
        : '入力途中の内容を復元しました。'
    );
    for (const delay of [0, 150, 500]) {
      window.setTimeout(() => {
        if (!form.isConnected) return;
        form.compositionRaw?.dispatchEvent(new Event('input', { bubbles: true }));
      }, delay);
    }
  }

  function initializeEditorForm(form) {
    if (form === activeForm) return;
    activeForm = form;
    const initialValues = serializableFormValues(form);
    form.dataset.initialFingerprint = fingerprint(initialValues);
    form.dataset.saveInFlight = 'false';
    form.dataset.hasPendingFiles = 'false';

    const draft = readEditorDraft();
    if (draft?.fingerprint === form.dataset.initialFingerprint && draft.values) {
      applyEditorDraft(form, draft);
    }
  }

  document.addEventListener('input', (event) => {
    const form = event.target.closest?.(`#${FORM_ID}`);
    if (!form) return;
    initializeEditorForm(form);
    scheduleEditorDraft(form);
  }, true);

  document.addEventListener('change', (event) => {
    const form = event.target.closest?.(`#${FORM_ID}`);
    if (!form) return;
    initializeEditorForm(form);
    if (event.target.type === 'file' && event.target.files?.length) {
      form.dataset.hasPendingFiles = 'true';
    }
    scheduleEditorDraft(form);
  }, true);

  document.addEventListener('click', (event) => {
    const directSend = event.target.closest?.('[data-send]');
    if (directSend) {
      const card = directSend.closest('.record');
      const item = card ? handoffForVersion(directSend.dataset.send, recordVersion(card)) : null;
      if (item) {
        event.preventDefault();
        event.stopImmediatePropagation();
        refreshRecordSendState(card);
        return;
      }
      directSend.disabled = true;
      directSend.setAttribute('aria-busy', 'true');
      directSend.textContent = '送信中…';
      queueMicrotask(() => refreshRecordSendState(card || document));
      return;
    }

    const saveAndSend = event.target.closest?.('#saveAndSend');
    if (!saveAndSend) return;
    const form = saveAndSend.closest(`#${FORM_ID}`);
    if (!form) return;
    initializeEditorForm(form);
    if (!form.checkValidity()) {
      event.preventDefault();
      event.stopImmediatePropagation();
      form.reportValidity();
      setFormBusy(form, false);
      setFormMessage(form, '入力内容を確認してください。DRAFT保存と送信はまだ実行されていません。', true);
    }
  }, true);

  document.addEventListener('submit', (event) => {
    const form = event.target;
    if (!(form instanceof HTMLFormElement) || form.id !== FORM_ID) return;
    initializeEditorForm(form);
    setFormBusy(form, true);
    setFormMessage(form, '保存しています。完了するまでボタンは再操作できません。');

    queueMicrotask(() => {
      if (!form.isConnected) return;
      const message = formMessage(form)?.textContent || '';
      if (message.includes('写真または対象情報を入力してください')) {
        setFormBusy(form, false);
        setFormMessage(form, message, true);
      }
    });
  }, true);

  window.addEventListener('unhandledrejection', (event) => {
    const form = document.getElementById(FORM_ID);
    if (!form || form.dataset.saveInFlight !== 'true') return;
    setFormBusy(form, false);
    setFormMessage(form, `保存できませんでした: ${event.reason?.message || '保存処理でエラーが発生しました'}`, true);
  });

  function normalizedText(element) {
    return (element?.textContent || '').replace(/\s+/g, ' ').trim();
  }

  function photoCaptureHeader() {
    const heading = [...document.querySelectorAll('h1')]
      .find((element) => normalizedText(element).includes('Knit Compass Photo Capture'));
    if (!heading) return null;
    return heading.closest('section,.card,header') || heading.parentElement?.parentElement || heading.parentElement;
  }

  function exactLabeledElement(root, labels) {
    if (!root) return null;
    return [...root.querySelectorAll('a,button,span')]
      .find((element) => !element.children.length && labels.has(normalizedText(element))) || null;
  }

  function statusOnly(element) {
    if (!element || !element.matches('a,button,[role="button"]')) return element;
    const status = document.createElement('span');
    status.className = element.className || 'badge';
    status.textContent = normalizedText(element);
    status.setAttribute('aria-label', `${status.textContent}（状態表示）`);
    status.dataset.kcStatusOnly = 'true';
    element.replaceWith(status);
    return status;
  }

  function reviewInboxHref() {
    return window.location.pathname.includes('/photo-capture-current/')
      ? '../brand-intelligence/'
      : 'brand-intelligence/';
  }

  function reviewInboxLink(element, fallbackClass = 'badge') {
    const link = element?.tagName === 'A' ? element : document.createElement('a');
    if (link !== element) {
      link.className = element?.className || fallbackClass;
      element?.replaceWith(link);
    }
    link.href = reviewInboxHref();
    link.textContent = '受信箱で内容確認';
    link.title = 'Human Review受信箱を開く';
    link.dataset.kcReviewInboxAction = 'true';
    link.removeAttribute('disabled');
    link.removeAttribute('aria-disabled');
    link.removeAttribute('role');
    return link;
  }

  function refreshTopWorkflowControls() {
    const header = photoCaptureHeader();
    if (!header) return;

    const draft = statusOnly(exactLabeledElement(header, DRAFT_STATUS_LABELS));
    const formal = statusOnly(exactLabeledElement(header, FORMAL_STATUS_LABELS));
    const existingAction = exactLabeledElement(header, REVIEW_ACTION_LABELS);

    if (existingAction) {
      reviewInboxLink(existingAction);
      return;
    }

    if (header.querySelector('[data-kc-review-inbox-action="true"]')) return;

    const host = header.querySelector('.badges')
      || (draft && formal && draft.parentElement === formal.parentElement ? draft.parentElement : null);
    if (!host) return;

    const link = reviewInboxLink(null, draft?.className || formal?.className || 'badge');
    if (draft?.parentElement === host) draft.insertAdjacentElement('afterend', link);
    else host.append(link);
  }

  const observer = new MutationObserver(() => {
    const form = document.getElementById(FORM_ID);
    if (form) initializeEditorForm(form);
    if (activeForm && !activeForm.isConnected && activeForm.dataset.saveInFlight === 'true') {
      sessionStorage.removeItem(EDITOR_DRAFT_KEY);
      activeForm = null;
    }
    refreshRecordSendState();
    refreshTopWorkflowControls();
  });

  const observerRoot = document.documentElement;
  if (observerRoot?.isConnected) {
    try { observer.observe(observerRoot, { childList: true, subtree: true }); } catch { /* ページ離脱中 */ }
  }
  refreshRecordSendState();
  refreshTopWorkflowControls();
})();