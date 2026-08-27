(function knitCompassExhibitionBurstMode() {
  "use strict";

  const BUILD = "2.1.44-independent.13-v04-ui";
  const STORAGE_KEY = "kc_photo_capture_supplier_session_v1";
  const MAX_CONTEXT_AGE_MS = 18 * 60 * 60 * 1000;

  let renderQueued = false;

  function clean(value) {
    return String(value == null ? "" : value).trim();
  }

  function setText(node, value) {
    if (node && node.textContent !== value) node.textContent = value;
  }

  function setHidden(node, hidden) {
    if (node && node.hidden !== hidden) node.hidden = hidden;
  }

  function setDisabled(node, disabled) {
    if (node && node.disabled !== disabled) node.disabled = disabled;
  }

  function setAttributeIfChanged(node, name, value) {
    if (!node) return;
    if (value == null) {
      if (node.hasAttribute(name)) node.removeAttribute(name);
      return;
    }
    if (node.getAttribute(name) !== value) node.setAttribute(name, value);
  }

  function updateVisibleReleaseLabel() {
    const version = document.querySelector(".kc-build-info strong");
    setText(version, "2.1.44 独立版");

    const updated = document.querySelector(".kc-build-info time");
    if (updated) {
      setText(updated, "2026-08-27 20:40 CST");
      setAttributeIfChanged(updated, "datetime", "2026-08-27T20:40:00+08:00");
    }

    const lead = document.querySelector(".kc-lead");
    if (lead && lead.textContent.includes("Photo Capture 2.1.43")) {
      setText(
        lead,
        "Photo Capture 2.1.44の現行画面です。展示会ではメーカーを一度選ぶと、同じメーカーの写真・素材登録へ引き継げます。写真と素材情報は端末へDRAFT保存し、必要な記録だけを外部取込ZIPとして書き出します。正式マスターへの反映は確認後に行います。"
      );
    }
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

    if (visitInput.value !== context.visitContext) {
      visitInput.value = context.visitContext;
      dispatchFieldEvent(visitInput, "input");
      dispatchFieldEvent(visitInput, "change");
    }

    window.setTimeout(() => {
      const currentForm = captureForm();
      if (!currentForm || !isNewRecord(currentForm)) return;
      const currentSupplierInput = currentForm.elements?.supplier;
      if (!currentSupplierInput) return;
      if (currentSupplierInput.value !== context.supplier) {
        currentSupplierInput.value = context.supplier;
        dispatchFieldEvent(currentSupplierInput, "input");
        dispatchFieldEvent(currentSupplierInput, "change");
      }
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
    const nextLabel = context ? "同じメーカーで次を登録" : button.dataset.kcOriginalLabel;
    setText(button, nextLabel);
    setAttributeIfChanged(
      button,
      "aria-label",
      context ? `${context.supplier}を引き継いで新しい素材・写真を登録` : null
    );
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
      if (panel.dataset.active !== "true") panel.dataset.active = "true";
      setText(title, "メーカー固定中");
      setText(summary, `${stored.visitContext} / ${stored.supplier}`);
      if (lockButton) {
        const same = Boolean(current && current.visitContext === stored.visitContext && current.supplier === stored.supplier);
        setText(lockButton, same ? "固定済み" : "この入力内容で固定を更新");
        setDisabled(lockButton, same);
      }
      setHidden(changeButton, false);
    } else {
      if (panel.dataset.active !== "false") panel.dataset.active = "false";
      setText(title, "メーカー連続撮影");
      setText(summary, "展示会・訪問先とメーカーを一度選ぶと、次の新規登録にも引き継ぎます。");
      if (lockButton) {
        setText(lockButton, "現在のメーカーを固定");
        setDisabled(lockButton, !current);
      }
      setHidden(changeButton, true);
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
    updateVisibleReleaseLabel();
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

  const appRoot = document.getElementById("app") || document.documentElement;
  const observer = new MutationObserver(queueEnsure);
  observer.observe(appRoot, {
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
