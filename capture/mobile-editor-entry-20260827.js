(() => {
  'use strict';

  const STORAGE_KEY = 'kc_photo_capture_supplier_session_v1';
  const root = document.getElementById('app');
  if (!root) return;

  let queued = false;

  function clean(value) {
    return String(value == null ? '' : value).trim();
  }

  function storedContext() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const visitContext = clean(parsed.visitContext);
      const supplier = clean(parsed.supplier);
      return visitContext && supplier ? { visitContext, supplier } : null;
    } catch (_error) {
      return null;
    }
  }

  function setIfPresent(form, name, value) {
    const control = form?.elements?.[name];
    if (!control || value == null) return;
    try { control.value = value; } catch (_error) {}
  }

  function dispatch(control, type) {
    if (!control) return;
    control.dispatchEvent(new Event(type, { bubbles: true }));
  }

  function placeEditorFirst() {
    const editor = document.getElementById('kcEditor');
    const inbox = document.getElementById('kcInbox');
    if (!editor || !inbox || editor.parentNode !== inbox.parentNode) return;
    if (editor.nextElementSibling !== inbox) {
      inbox.parentNode.insertBefore(editor, inbox);
    }
  }

  function showEditorNow() {
    const editor = document.getElementById('kcEditor');
    if (!editor || editor.hidden) return false;
    placeEditorFirst();
    editor.scrollIntoView({ behavior: 'auto', block: 'start' });
    return true;
  }

  function fallbackOpenNewCapture() {
    const editor = document.getElementById('kcEditor');
    const form = document.getElementById('kcCaptureForm');
    if (!editor || !form || !editor.hidden) return;

    try { form.reset(); } catch (_error) {}
    setIfPresent(form, 'record_id', '');
    setIfPresent(form, 'priority', 'NORMAL');
    setIfPresent(form, 'attention_rating', '★（参考）');
    setIfPresent(form, 'data_state', 'DRAFT');
    setIfPresent(form, 'human_review_status', 'NOT_REVIEWED');
    setIfPresent(form, 'currency', 'CNY');
    setIfPresent(form, 'price_unit', 'kg');
    setIfPresent(form, 'functional_fiber_usage', '未確認');
    setIfPresent(form, 'sustainable_fiber_usage', '未確認');
    setIfPresent(form, 'research_request', '不要');
    setIfPresent(form, 'book_request', '未確認');
    setIfPresent(form, 'fabric_request', '未確認');

    const context = storedContext();
    if (context) {
      setIfPresent(form, 'visit_context', context.visitContext);
      dispatch(form.elements?.visit_context, 'input');
      dispatch(form.elements?.visit_context, 'change');
      setIfPresent(form, 'supplier', context.supplier);
      dispatch(form.elements?.supplier, 'input');
      dispatch(form.elements?.supplier, 'change');
    }

    const title = document.getElementById('kcEditorTitle');
    if (title) title.textContent = '新規キャプチャ';
    const message = document.getElementById('kcEditorMessage');
    if (message) {
      message.textContent = context
        ? `${context.supplier}を引き継いで新しい素材・写真を登録します。`
        : '写真または糸情報を入力してDRAFT保存してください。';
      message.classList.remove('error');
    }

    editor.hidden = false;
    placeEditorFirst();
    editor.scrollIntoView({ behavior: 'auto', block: 'start' });
  }

  function ensureEditorPlacement() {
    const editor = document.getElementById('kcEditor');
    if (!editor || editor.hidden) return;
    showEditorNow();
  }

  function queueEnsure() {
    if (queued) return;
    queued = true;
    queueMicrotask(() => {
      queued = false;
      ensureEditorPlacement();
    });
  }

  document.addEventListener('click', (event) => {
    const button = event.target.closest?.('#kcNewCapture, [data-empty-create]');
    if (!button) return;

    // Let the native Photo Capture handler run first. If it throws or the very
    // long inbox prevents a visible transition on Android, recover immediately.
    window.setTimeout(() => {
      if (!showEditorNow()) fallbackOpenNewCapture();
    }, 80);
  }, true);

  const observer = new MutationObserver(queueEnsure);
  observer.observe(root, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['hidden']
  });
  queueEnsure();
})();
