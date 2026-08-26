(function knitCompassExhibitionBurstMode() {
  "use strict";

  const BUILD = "2.1.44-independent.1";
  const STORAGE_KEY = "kc_photo_capture_supplier_session_v1";
  const MAX_CONTEXT_AGE_MS = 18 * 60 * 60 * 1000;

  let renderQueued = false;

  function clean(value) {
    return String(value == null ? "" : value).trim();
  }

  function readContext() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const savedAt = Number(parsed.savedAt || 0);
      if (!savedAt || Date.now() - savedAt > MAX_CONTEXT_AGE_MS) {
        localStorage.removeItem(STORAGE_KEY);
        return null;
      }
      const visitContext = clean(parsed.visitContext);
      const supplier = clean(parsed.supplier);
      if (!visitContext || !supplier) return null;
      return { visitContext, supplier, savedAt };
    } catch (_error) {
      return null;
    }
  }

  function writeContext(visitContext, supplier) {
    const next = {
      visitContext: clean(visitContext),
      supplier: clean(supplier),
      savedAt: Date.now(),
      build: BUILD
    };
    if (!next.visitContext || !next.supplier) return null;
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (_error) {
      return null;
    }
    return next;
  }

  function clearContext() {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (_error) {
      // Device-local convenience state only. Failure must not block capture.
    }
  }

  function captureForm() {
    return document.getElementById("kcCaptureForm");
  }

  function isNewRecord(form) {
    return !clean(form?.elements?.record_id?.value);
  }

  function currentContextFromForm(form) {
    if (!form) return null;
    const visitContext = clean(form.elements?.visit_context?.value);
    const supplier = clean(form.elements?.supplier?.value);
    if (!visitContext || !supplier) return null;
    return { visitContext, supplier };
  }

  function persistCurrentContext() {
    const form = captureForm();
    const context = currentContextFromForm(form);
    if (!context) return null;
    return writeContext(context.visitContext, context.supplier);
  }

  function dispatchFieldEvent(input, type) {
    input.dispatchEvent(new Event(type, { bubbles: true }));
  }

  function applyStoredContextToNewRecord({ force = false } = {}) {
    const form = captureForm();
    const context = readContext();
    if (!form || !context || !isNewRecord(form)) return;

    const visitInput = form.elements?.visit_context;
    const supplierInput = form.elements?.supplier;
    if (!visitInput || !supplierInput) return;

    const currentVisit = clean(visitInput.value);
    const currentSupplier = clean(supplierInput.value);
    if (!force && (currentVisit || currentSupplier)) return;

    visitInput.value = context.visitContext;
    dispatchFieldEvent(visitInput, "input");
    dispatchFieldEvent(visitInput, "change");

    window.setTimeout(() => {
      const currentForm = captureForm();
      if (!currentForm || !isNewRecord(currentForm)) return;
      const currentSupplierInput = currentForm.elements?.supplier;
      if (!currentSupplierInput) return;
      currentSupplierInput.value = context.supplier;
      dispatchFieldEvent(currentSupplierInput, "input");
      dispatchFieldEvent(currentSupplierInput, "change");
      ensureBurstUi();
    }, 0);
  }

  function panelMarkup() {
    const panel = document.createElement("section");
    panel.id = "kcExhibitionBurstPanel";
    panel.className = "kc-exhibition-burst-panel";
    panel.setAttribute("aria-live", "polite");
    panel.innerHTML = `
      <div class="kc-exhibition-burst-copy">
        <span class="kc-exhibition-burst-kicker">EXHIBITION QUICK CAPTURE</span>
        <strong id="kcExhibitionBurstTitle">メーカー連続撮影</strong>
        <p id="kcExhibitionBurstSummary">展示会・訪問先とメーカーを一度選ぶと、次の新規登録にも引き継ぎます。</p>
      </div>
      <div class="kc-exhibition-burst-actions">
        <button type="button" class="secondary" data-kc-burst-action="lock">現在のメーカーを固定</button>
        <button type="button" class="secondary" data-kc-burst-action="change">メーカー変更</button>
      </div>
      <p class="kc-exhibition-burst-note">同じメーカーでは写真を何枚でも続けて記録できます。1素材あたりの写真上限を超える場合や別素材に分ける場合は「新規登録」を使ってください。展示会・メーカー名は自動で残ります。</p>
    `;
    return panel;
  }

  function ensurePanel() {
    const form = captureForm();
    if (!form) return null;
    let panel = document.getElementById("kcExhibitionBurstPanel");
    if (panel) return panel;

    const supplierInput = form.elements?.supplier;
    const supplierLabel = supplierInput?.closest("label");
    if (!supplierLabel) return null;

    panel = panelMarkup();
    supplierLabel.insertAdjacentElement("afterend", panel);
    return panel;
  }

  function updateNewCaptureButton(context) {
    const button = document.getElementById("kcNewCapture");
    if (!button) return;
    if (!button.dataset.kcOriginalLabel) {
      button.dataset.kcOriginalLabel = clean(button.textContent) || "新規登録";
    }
    button.textContent = context ? "同じメーカーで次を登録" : button.dataset.kcOriginalLabel;
    if (context) {
      button.setAttribute("aria-label", `${context.supplier}を引き継いで新しい素材・写真を登録`);
    } else {
      button.removeAttribute("aria-label");
    }
  }

  function updatePanel() {
    const panel = ensurePanel();
    const form = captureForm();
    const stored = readContext();
    if (!panel || !form) {
      updateNewCaptureButton(stored);
      return;
    }

    const current = currentContextFromForm(form);
    const title = panel.querySelector("#kcExhibitionBurstTitle");
    const summary = panel.querySelector("#kcExhibitionBurstSummary");
    const lockButton = panel.querySelector('[data-kc-burst-action="lock"]');
    const changeButton = panel.querySelector('[data-kc-burst-action="change"]');

    if (stored) {
      panel.dataset.active = "true";
      if (title) title.textContent = "メーカー固定中";
      if (summary) summary.textContent = `${stored.visitContext} / ${stored.supplier}`;
      if (lockButton) {
        const same = Boolean(current && current.visitContext === stored.visitContext && current.supplier === stored.supplier);
        lockButton.textContent = same ? "固定済み" : "この入力内容で固定を更新";
        lockButton.disabled = same;
      }
      if (changeButton) changeButton.hidden = false;
    } else {
      panel.dataset.active = "false";
      if (title) title.textContent = "メーカー連続撮影";
      if (summary) summary.textContent = "展示会・訪問先とメーカーを一度選ぶと、次の新規登録にも引き継ぎます。";
      if (lockButton) {
        lockButton.textContent = "現在のメーカーを固定";
        lockButton.disabled = !current;
      }
      if (changeButton) changeButton.hidden = true;
    }

    updateNewCaptureButton(stored);
  }

  function addSupplierHint() {
    const form = captureForm();
    const supplierInput = form?.elements?.supplier;
    const label = supplierInput?.closest("label");
    if (!label || label.querySelector(".kc-exhibition-burst-inline-hint")) return;
    const hint = document.createElement("span");
    hint.className = "kc-field-hint kc-exhibition-burst-inline-hint";
    hint.textContent = "展示会ではメーカー名を一度選べば、次の新規登録にも自動で引き継ぎます。";
    label.appendChild(hint);
  }

  function ensureBurstUi() {
    addSupplierHint();
    updatePanel();
    const form = captureForm();
    if (form && isNewRecord(form)) applyStoredContextToNewRecord();
  }

  function queueEnsure() {
    if (renderQueued) return;
    renderQueued = true;
    window.requestAnimationFrame(() => {
      renderQueued = false;
      ensureBurstUi();
    });
  }

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) && !(target instanceof HTMLSelectElement)) return;
    if (!target.form || target.form.id !== "kcCaptureForm") return;
    if (!["visit_context", "supplier"].includes(target.name)) return;

    const context = currentContextFromForm(target.form);
    if (context) writeContext(context.visitContext, context.supplier);
    updatePanel();
  });

  document.addEventListener("blur", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.form || target.form.id !== "kcCaptureForm" || target.name !== "supplier") return;
    const context = currentContextFromForm(target.form);
    if (context) writeContext(context.visitContext, context.supplier);
    updatePanel();
  }, true);

  document.addEventListener("click", (event) => {
    const action = event.target.closest?.("[data-kc-burst-action]");
    if (action) {
      const form = captureForm();
      if (action.dataset.kcBurstAction === "lock") {
        const context = currentContextFromForm(form);
        if (!context) return;
        writeContext(context.visitContext, context.supplier);
        updatePanel();
        return;
      }
      if (action.dataset.kcBurstAction === "change") {
        clearContext();
        if (form && isNewRecord(form)) {
          if (form.elements?.supplier) form.elements.supplier.value = "";
          form.elements?.supplier?.focus();
        }
        updatePanel();
        return;
      }
    }

    const newCapture = event.target.closest?.("#kcNewCapture, [data-empty-create]");
    if (!newCapture) return;
    persistCurrentContext();
    window.setTimeout(() => {
      applyStoredContextToNewRecord({ force: true });
      ensureBurstUi();
    }, 0);
  }, true);

  const observer = new MutationObserver(queueEnsure);
  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["hidden"]
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", queueEnsure, { once: true });
  } else {
    queueEnsure();
  }
})();
