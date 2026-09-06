(function knitCompassSimpleSessionMode() {
  "use strict";

  const BUILD = "2.1.44-independent.14-save-next";
  const SESSION_KEY = "kc_photo_capture_simple_supplier_session_v1";
  const MODE_KEY = "kc_photo_capture_simple_mode_v1";
  const MAX_SESSION_AGE_MS = 18 * 60 * 60 * 1000;
  let renderQueued = false;
  let pendingSave = null;
  let savedCapture = null;
  let nextContext = null;
  let currentSequence = 1;
  let currentSupplier = "";
  let structure = null;

  const clean = (value) => String(value == null ? "" : value).trim();
  const byId = (id) => document.getElementById(id);
  const captureForm = () => byId("kcCaptureForm");
  const simpleMode = () => document.body.classList.contains("kc-simple-capture-mode");
  const isNewRecord = (form) => !clean(form?.elements?.record_id?.value);
  const sequenceLabel = (sequence) => `素材 ${String(sequence).padStart(2, "0")}`;
  function setText(node, value) { if (node && node.textContent !== value) node.textContent = value; }
  function setHidden(node, value) { if (node && node.hidden !== value) node.hidden = value; }

  function readSession() {
    try {
      const value = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
      if (!value || !clean(value.supplier) || !Number(value.savedAt) || Date.now() - Number(value.savedAt) > MAX_SESSION_AGE_MS) return null;
      return {
        supplier: clean(value.supplier), visitContext: clean(value.visitContext),
        sequence: Math.max(1, Math.floor(Number(value.sequence) || 1))
      };
    } catch (_error) { return null; }
  }

  function rememberSession(context) {
    try {
      if (!context?.supplier) localStorage.removeItem(SESSION_KEY);
      else localStorage.setItem(SESSION_KEY, JSON.stringify({ ...context, savedAt: Date.now(), build: BUILD }));
    } catch (_error) { /* Session convenience only; saved captures remain in IndexedDB. */ }
  }

  function setField(field, value) {
    if (!field || field.value === value) return;
    field.value = value;
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function preferredSimpleMode() {
    if (new URLSearchParams(location.search).get("full") === "1") return false;
    try { return localStorage.getItem(MODE_KEY) !== "full"; }
    catch (_error) { return true; }
  }

  function buildModeToggle() {
    if (byId("kcSimpleModeToggle")) return;
    // The legacy .kc-session is hidden by the capture shell.
    const host = document.querySelector(".kc-v04-header-inner") || document.querySelector(".kc-topbar");
    if (!host) return;
    const button = document.createElement("button");
    button.type = "button";
    button.id = "kcSimpleModeToggle";
    button.className = "secondary kc-simple-mode-toggle";
    button.dataset.simpleAction = "toggle-mode";
    host.appendChild(button);
  }

  function buildHistoryToggle() {
    if (byId("kcSimpleHistoryToggle")) return;
    const host = document.querySelector("#kcInbox .kc-primary-actions");
    if (!host) return;
    const button = document.createElement("button");
    button.type = "button";
    button.id = "kcSimpleHistoryToggle";
    button.className = "secondary";
    button.dataset.simpleAction = "history";
    host.appendChild(button);
  }

  function anchorFor(node) {
    const anchor = document.createComment("Original capture field position");
    node.before(anchor);
    return anchor;
  }

  function buildForm(form) {
    if (structure?.form === form) return;
    const basic = byId("kcBasicTitle")?.closest(".kc-form-section");
    const photo = byId("kcPhotoTitle")?.closest(".kc-form-section");
    const material = byId("kcMaterialTitle")?.closest(".kc-form-section");
    const supplier = form.elements?.supplier?.closest("label");
    const originalActions = form.querySelector(".kc-form-actions");
    if (!basic || !photo || !material || !supplier || !originalActions) return;
    structure = {
      form, basic, photo, material, supplier,
      supplierAnchor: anchorFor(supplier), basicAnchor: anchorFor(basic), materialAnchor: anchorFor(material),
      supplierLabel: supplier.firstChild, originalSupplierLabel: supplier.firstChild.textContent
    };
    const keepBasic = new Set(["entry_date", "visit_context", "yarn_name"]);
    const keepMaterial = new Set(["yarn_count", "composition", "notes"]);
    [basic, material].forEach((section) => {
      section.querySelectorAll("label.kc-company-question, fieldset.kc-company-question").forEach((block) => {
        if (block === supplier) return;
        const control = block.querySelector("input[name], select[name], textarea[name]");
        if (!control || !(section === basic ? keepBasic : keepMaterial).has(control.name)) block.classList.add("kc-simple-hidden-field");
      });
    });
    ["kcActionTitle", "kcResearchTitle"].forEach((id) => byId(id)?.closest(".kc-form-section")?.classList.add("kc-simple-hidden-section"));
    form.querySelector(".kc-kc-details")?.classList.add("kc-simple-hidden-section");
    form.querySelector(".kc-policy")?.classList.add("kc-simple-hidden-section");
    originalActions.classList.add("kc-simple-original-actions");
    photo.classList.add("kc-simple-section-photo");
    [".kc-primary-photo-slot", ".kc-photo-category-guide", ".kc-photo-grid"].forEach((selector) => photo.querySelector(selector)?.classList.add("kc-simple-photo-original"));

    const session = document.createElement("section");
    session.id = "kcSimpleSessionPanel";
    session.className = "kc-simple-session-panel";
    basic.before(session);
    const info = document.createElement("details");
    info.id = "kcSimpleInfoDetails";
    info.innerHTML = `<summary>素材情報を入力（任意）</summary><div id="kcSimpleInfoFields"></div><button type="button" class="ghost" data-simple-action="details">詳細入力</button>`;
    photo.after(info);
    const quick = document.createElement("div");
    quick.id = "kcSimpleQuickPhoto";
    quick.innerHTML = `
      <div class="kc-simple-quick-photo-heading">
        <h3 id="kcSimpleSequence">素材 01</h3><span id="kcSimplePhotoCount">0 / 10枚</span>
      </div>
      <div class="kc-simple-photo-actions">
        <label class="kc-simple-camera-button">撮影
          <input class="kc-visually-hidden-file" type="file" accept="image/*" capture="environment" data-photo-input="other" data-photo-source="camera">
        </label>
        <label class="kc-simple-library-button">写真からまとめて選択
          <input class="kc-visually-hidden-file" type="file" accept="image/*" multiple data-photo-input="other" data-photo-source="library">
        </label>
      </div>
      <div id="kcSimpleQuickPreview" class="kc-simple-quick-preview"></div>`;
    photo.prepend(quick);
    const actions = document.createElement("div");
    actions.id = "kcSimpleActions";
    actions.innerHTML = `<button type="button" data-simple-action="save" id="kcSimpleSave">保存</button>`;
    originalActions.before(actions);
  }

  function arrangeForm() {
    if (!structure) return;
    const { supplier, basic, material, supplierAnchor, basicAnchor, materialAnchor, supplierLabel, originalSupplierLabel } = structure;
    if (simpleMode()) {
      const session = byId("kcSimpleSessionPanel");
      const info = byId("kcSimpleInfoFields");
      if (supplier.parentElement !== session) session.appendChild(supplier);
      if (basic.parentElement !== info) info.appendChild(basic);
      if (material.parentElement !== info) info.appendChild(material);
      if (supplierLabel.textContent !== "メーカー／糸商") supplierLabel.textContent = "メーカー／糸商";
    } else {
      [[supplier, supplierAnchor], [basic, basicAnchor], [material, materialAnchor]].forEach(([node, anchor]) => {
        if (anchor.nextSibling !== node) anchor.after(node);
      });
      if (supplierLabel.textContent !== originalSupplierLabel) supplierLabel.textContent = originalSupplierLabel;
    }
  }

  function buildSavedPanel() {
    if (byId("kcSimpleSavedPanel") || !byId("kcEditor")) return;
    const panel = document.createElement("section");
    panel.id = "kcSimpleSavedPanel";
    panel.className = "kc-panel";
    panel.hidden = true;
    panel.setAttribute("aria-labelledby", "kcSimpleSavedTitle");
    panel.innerHTML = `
      <p class="kc-simple-saved-status" role="status">端末に保存しました</p>
      <h2 id="kcSimpleSavedTitle">次の撮影へ</h2>
      <p id="kcSimpleSavedSummary"></p>
      <div class="kc-simple-saved-actions">
        <button type="button" data-simple-action="next-supplier">次のメーカー／糸商</button>
        <button type="button" class="secondary" data-simple-action="next-material">同じメーカーで次の素材<span id="kcSimpleNextSummary"></span></button>
        <button type="button" class="ghost" data-simple-action="finish">撮影を終了</button>
      </div>`;
    byId("kcEditor").after(panel);
  }

  function photoCount() {
    return Number(clean(byId("kcPhotoCount")?.textContent).match(/^(\d+)/)?.[1] || 0);
  }

  function updatePreview() {
    setText(byId("kcSimplePhotoCount"), `${photoCount()} / 10枚`);
    const target = byId("kcSimpleQuickPreview");
    if (!target) return;
    const images = [...captureForm().querySelectorAll("[data-photo-preview] img")];
    const signature = images.map((image) => image.src).join("|") || "__empty__";
    if (target.dataset.signature === signature) return;
    target.dataset.signature = signature;
    target.replaceChildren();
    if (!images.length) {
      const empty = document.createElement("span");
      empty.textContent = "写真はまだありません";
      target.appendChild(empty);
    }
    images.forEach((image) => {
      const clone = document.createElement("img");
      clone.src = image.src;
      clone.alt = "撮影済み写真";
      target.appendChild(clone);
    });
  }

  function updateControls() {
    const source = byId("kcSaveDraft");
    const busy = Boolean(source?.disabled || pendingSave);
    const save = byId("kcSimpleSave");
    if (save) {
      if (save.disabled !== busy) save.disabled = busy;
      setText(save, pendingSave ? "保存中…" : source?.disabled ? "写真を処理中…" : "保存");
    }
    const toggle = byId("kcSimpleModeToggle");
    if (toggle) {
      setText(toggle, simpleMode() ? "通常画面" : "シンプル撮影");
      if (toggle.disabled !== busy) toggle.disabled = busy;
    }
    setText(byId("kcSimpleHistoryToggle"), document.body.classList.contains("kc-simple-history-open") ? "保存済みを閉じる" : "保存済みを見る");
    document.querySelectorAll('[data-simple-action="details"]').forEach((button) => setText(button, document.body.classList.contains("kc-simple-show-details") ? "詳細入力を閉じる" : "詳細入力"));
    setHidden(byId("kcSimpleSavedPanel"), !savedCapture || !simpleMode());
    document.body.classList.toggle("kc-simple-after-save", Boolean(savedCapture && simpleMode()));
    document.body.classList.toggle("kc-simple-editing", Boolean(simpleMode() && byId("kcEditor") && !byId("kcEditor").hidden));
    const form = captureForm();
    if (form) {
      const supplier = clean(form.elements.supplier.value);
      if (isNewRecord(form) && supplier !== currentSupplier) {
        currentSupplier = supplier;
        const session = readSession();
        currentSequence = session?.supplier === supplier ? session.sequence : 1;
      }
      setText(byId("kcSimpleSequence"), isNewRecord(form) ? sequenceLabel(currentSequence) : "保存済み素材を編集");
    }
  }

  function updateCopy() {
    const heading = document.querySelector(".kc-brand h1");
    const lead = document.querySelector(".kc-brand .kc-lead");
    [heading, lead].forEach((node) => { if (node && !node.dataset.kcOriginalCopy) node.dataset.kcOriginalCopy = node.textContent; });
    setText(heading, simpleMode() ? "Photo Capture" : heading?.dataset.kcOriginalCopy);
    setText(lead, simpleMode() ? "メーカー／糸商を選んで撮影。保存したら、次のメーカーや素材へ進めます。" : lead?.dataset.kcOriginalCopy);
  }

  function ensureUi() {
    buildModeToggle();
    buildHistoryToggle();
    const form = captureForm();
    if (form) { buildForm(form); arrangeForm(); updatePreview(); }
    buildSavedPanel();
    updateControls();
    updateCopy();
  }

  function queueEnsure() {
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(() => { renderQueued = false; ensureUi(); });
  }

  function startSave() {
    const form = captureForm();
    const source = byId("kcSaveDraft");
    if (!form || pendingSave || !source || source.disabled) return;
    const supplier = clean(form.elements.supplier.value);
    const message = byId("kcEditorMessage");
    if (!supplier || !photoCount()) {
      setText(message, !supplier ? "メーカー／糸商を選択または入力してください。" : "この素材の写真を1枚以上追加してください。");
      message?.classList.add("error");
      if (!supplier) form.elements.supplier.focus();
      else byId("kcSimpleQuickPhoto")?.scrollIntoView({ block: "center", behavior: "smooth" });
      return;
    }
    pendingSave = { sequence: isNewRecord(form) ? currentSequence : null };
    updateControls();
    source.click();
  }

  function openNext(sameSupplier) {
    if (!savedCapture) return;
    const saved = savedCapture;
    savedCapture = null;
    nextContext = {
      supplier: sameSupplier ? saved.supplier : "",
      visitContext: saved.visitContext,
      sequence: sameSupplier ? saved.nextSequence : 1,
      focusSupplier: !sameSupplier
    };
    rememberSession(sameSupplier ? nextContext : null);
    updateControls();
    byId("kcNewCapture")?.click();
  }

  document.addEventListener("kc:capture-opened", () => {
    ensureUi();
    savedCapture = null;
    const form = captureForm();
    const context = nextContext || (simpleMode() && isNewRecord(form) ? readSession() : null);
    nextContext = null;
    if (context && isNewRecord(form)) {
      // Fill once when opening. Typing or clearing a field never restores stale values.
      currentSupplier = context.supplier;
      currentSequence = context.sequence;
      setField(form.elements.visit_context, context.visitContext);
      setField(form.elements.supplier, context.supplier);
      currentSupplier = context.supplier;
      currentSequence = context.sequence;
      if (context.focusSupplier) form.elements.supplier.focus({ preventScroll: true });
    } else { currentSupplier = clean(form.elements.supplier.value); currentSequence = 1; }
    if (byId("kcSimpleInfoDetails")) byId("kcSimpleInfoDetails").open = false;
    document.body.classList.remove("kc-simple-show-details");
    updateControls();
  });

  document.addEventListener("kc:capture-saved", (event) => {
    if (!pendingSave || !simpleMode()) return;
    const { supplier, visitContext, photoCount: count, eventType } = event.detail;
    const session = readSession();
    const nextSequence = pendingSave.sequence == null
      ? (session?.supplier === supplier ? session.sequence : 1)
      : pendingSave.sequence + 1;
    savedCapture = { supplier, visitContext, nextSequence };
    const label = pendingSave.sequence == null ? "保存済み素材" : sequenceLabel(pendingSave.sequence);
    setText(byId("kcSimpleSavedSummary"), `${supplier} · ${label} · 写真${count}枚`);
    setText(byId("kcSimpleNextSummary"), `${supplier} · ${sequenceLabel(nextSequence)}へ`);
    if (eventType === "CREATE") rememberSession({ supplier, visitContext, sequence: nextSequence });
    updateControls();
    byId("kcSimpleSavedPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  document.addEventListener("kc:capture-save-finished", () => { pendingSave = null; updateControls(); });

  document.addEventListener("click", (event) => {
    const action = event.target.closest?.("[data-simple-action]");
    if (!action || action.disabled) return;
    switch (action.dataset.simpleAction) {
      case "toggle-mode": {
        const enabled = !simpleMode();
        document.body.classList.toggle("kc-simple-capture-mode", enabled);
        document.body.classList.remove("kc-simple-show-details");
        try { localStorage.setItem(MODE_KEY, enabled ? "simple" : "full"); } catch (_error) {}
        ensureUi();
        break;
      }
      case "history": document.body.classList.toggle("kc-simple-history-open"); updateControls(); break;
      case "details": document.body.classList.toggle("kc-simple-show-details"); updateControls(); break;
      case "save": startSave(); break;
      case "next-supplier": openNext(false); break;
      case "next-material": openNext(true); break;
      case "finish":
        savedCapture = null;
        rememberSession(null);
        updateControls();
        byId("kcInbox")?.scrollIntoView({ behavior: "smooth", block: "start" });
        break;
    }
  });
  document.addEventListener("input", (event) => { if (event.target.form?.id === "kcCaptureForm") updateControls(); });
  document.addEventListener("change", queueEnsure);
  new MutationObserver(queueEnsure).observe(byId("app") || document.documentElement, {
    childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "disabled"]
  });
  if (preferredSimpleMode()) document.body.classList.add("kc-simple-capture-mode");
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", queueEnsure, { once: true });
  else queueEnsure();
})();
