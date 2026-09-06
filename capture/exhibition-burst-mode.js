(function knitCompassSimpleCapture() {
  "use strict";
  const SESSION_KEY = "kc_photo_capture_simple_supplier_session_v1";
  const MODE_KEY = "kc_photo_capture_simple_mode_v1";
  const BUILD = "2.1.44-independent.15-basic-photo";
  const byId = id => document.getElementById(id);
  const clean = value => String(value == null ? "" : value).trim();
  const simpleMode = () => document.body.classList.contains("kc-simple-capture-mode");
  let queued = false;
  let pendingSave = null;
  let savedResult = null;
  let nextContext = null;

  function setText(node, value) { if (node && node.textContent !== value) node.textContent = value; }
  function readSession() {
    try {
      const saved = JSON.parse(localStorage.getItem(SESSION_KEY) || "null");
      return saved?.supplier && Date.now() - Number(saved.savedAt) < 18 * 60 * 60 * 1000 ? saved : null;
    } catch (_error) { return null; }
  }
  function rememberSession(context) {
    try {
      if (!context) localStorage.removeItem(SESSION_KEY);
      else localStorage.setItem(SESSION_KEY, JSON.stringify({ supplier: context.supplier, visitContext: context.visitContext, sequence: 1, savedAt: Date.now(), build: BUILD }));
    } catch (_error) { /* Convenience only; capture records are not changed here. */ }
  }
  function setField(field, value) {
    if (!field || field.value === value) return;
    field.value = value;
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  }
  function preferredSimpleMode() {
    if (new URLSearchParams(location.search).get("full") === "1") return false;
    try { return localStorage.getItem(MODE_KEY) !== "full"; } catch (_error) { return true; }
  }
  function buildButtons() {
    if (!byId("kcSimpleModeToggle")) {
      const host = document.querySelector(".kc-v04-header-inner") || document.querySelector(".kc-topbar");
      if (host) {
        const button = document.createElement("button");
        button.type = "button"; button.id = "kcSimpleModeToggle";
        button.className = "secondary kc-simple-mode-toggle"; button.dataset.simpleAction = "toggle-mode";
        host.appendChild(button);
      }
    }
    if (!byId("kcSimpleHistoryToggle")) {
      const host = document.querySelector("#kcInbox .kc-primary-actions");
      if (host) {
        const button = document.createElement("button");
        button.type = "button"; button.id = "kcSimpleHistoryToggle";
        button.className = "secondary"; button.dataset.simpleAction = "history";
        host.appendChild(button);
      }
    }
  }
  function buildForm(form) {
    if (byId("kcSimpleQuickPhoto")) return;
    const photo = byId("kcPhotoTitle")?.closest(".kc-form-section");
    const originalActions = form.querySelector(".kc-form-actions");
    if (!photo || !originalActions) return;
    // Basic fields remain in their original positions, with their original labels and values.
    const material = byId("kcMaterialTitle")?.closest(".kc-form-section");
    const keepMaterial = new Set(["yarn_count", "composition", "notes"]);
    material?.querySelectorAll("label.kc-company-question, fieldset.kc-company-question").forEach(block => {
      const control = block.querySelector("input[name], select[name], textarea[name]");
      if (!control || !keepMaterial.has(control.name)) block.classList.add("kc-simple-hidden-field");
    });
    ["kcActionTitle", "kcResearchTitle"].forEach(id => byId(id)?.closest(".kc-form-section")?.classList.add("kc-simple-hidden-section"));
    form.querySelector(".kc-kc-details")?.classList.add("kc-simple-hidden-section");
    form.querySelector(".kc-policy")?.classList.add("kc-simple-hidden-section");
    originalActions.classList.add("kc-simple-original-actions");
    photo.classList.add("kc-simple-section-photo");
    [".kc-primary-photo-slot", ".kc-photo-category-guide", ".kc-photo-grid"].forEach(selector => photo.querySelector(selector)?.classList.add("kc-simple-photo-original"));
    const quick = document.createElement("div");
    quick.id = "kcSimpleQuickPhoto";
    quick.innerHTML = `
      <div class="kc-simple-quick-photo-heading"><span>写真を続けて追加できます</span><span id="kcSimplePhotoCount">0 / 10枚</span></div>
      <div class="kc-simple-photo-actions">
        <label class="kc-simple-camera-button">撮影
          <input class="kc-visually-hidden-file" type="file" accept="image/*" capture="environment" data-photo-input="other" data-photo-source="camera">
        </label>
        <label class="kc-simple-library-button">写真からまとめて選択
          <input class="kc-visually-hidden-file" type="file" accept="image/*" multiple data-photo-input="other" data-photo-source="library">
        </label>
      </div>
      <div id="kcSimpleQuickPreview" class="kc-simple-quick-preview"></div>
      <button type="button" class="ghost" data-simple-action="details">詳細入力・写真の調整</button>`;
    photo.querySelector(".kc-section-heading").after(quick);
    const actions = document.createElement("div");
    actions.id = "kcSimpleActions";
    actions.innerHTML = `<button type="button" id="kcSimpleSave" data-simple-action="save">保存・終了</button><button type="button" class="secondary" id="kcSimpleNextSupplier" data-simple-action="save-next">保存・次の糸商</button>`;
    originalActions.before(actions);
  }
  function photoCount() { return Number(clean(byId("kcPhotoCount")?.textContent).match(/^(\d+)/)?.[1] || 0); }
  function updatePreview() {
    setText(byId("kcSimplePhotoCount"), `${photoCount()} / 10枚`);
    const target = byId("kcSimpleQuickPreview");
    const form = byId("kcCaptureForm");
    if (!target || !form) return;
    const images = [...form.querySelectorAll("[data-photo-preview] img")];
    const signature = images.map(image => image.src).join("|") || "__empty__";
    if (target.dataset.signature === signature) return;
    target.dataset.signature = signature;
    target.replaceChildren();
    if (!images.length) { const empty = document.createElement("span"); empty.textContent = "写真はまだありません"; target.appendChild(empty); }
    images.forEach(image => { const clone = document.createElement("img"); clone.src = image.src; clone.alt = "撮影済み写真"; target.appendChild(clone); });
  }
  function updateControls() {
    const source = byId("kcSaveDraft");
    const busy = Boolean(source?.disabled || pendingSave);
    ["kcSimpleSave", "kcSimpleNextSupplier", "kcSimpleModeToggle"].forEach(id => { const button = byId(id); if (button && button.disabled !== busy) button.disabled = busy; });
    setText(byId("kcSimpleSave"), pendingSave === "save" ? "保存中…" : source?.disabled ? "処理中…" : "保存・終了");
    setText(byId("kcSimpleNextSupplier"), pendingSave === "save-next" ? "保存中…" : "保存・次の糸商");
    setText(byId("kcSimpleModeToggle"), simpleMode() ? "通常画面" : "シンプル撮影");
    setText(byId("kcSimpleHistoryToggle"), document.body.classList.contains("kc-simple-history-open") ? "保存済みを閉じる" : "保存済みを見る");
    document.querySelectorAll('[data-simple-action="details"]').forEach(button => setText(button, document.body.classList.contains("kc-simple-show-details") ? "詳細入力を閉じる" : "詳細入力・写真の調整"));
    document.body.classList.toggle("kc-simple-editing", Boolean(simpleMode() && byId("kcEditor") && !byId("kcEditor").hidden));
    const photoTitle = byId("kcPhotoTitle");
    if (photoTitle?.firstChild?.nodeType === 3) {
      const text = simpleMode() ? "2. 写真登録 " : "2. 写真 ";
      if (photoTitle.firstChild.textContent !== text) photoTitle.firstChild.textContent = text;
    }
  }
  function updateCopy() {
    const heading = document.querySelector(".kc-brand h1");
    const lead = document.querySelector(".kc-brand .kc-lead");
    [heading, lead].forEach(node => { if (node && !node.dataset.kcOriginalCopy) node.dataset.kcOriginalCopy = node.textContent; });
    setText(heading, simpleMode() ? "Photo Capture" : heading?.dataset.kcOriginalCopy);
    setText(lead, simpleMode() ? "基本項目を入力し、写真を続けて追加します。撮影後は保存、または保存して次の糸商へ進めます。" : lead?.dataset.kcOriginalCopy);
  }
  function ensureUi() { buildButtons(); const form = byId("kcCaptureForm"); if (form) buildForm(form); updatePreview(); updateControls(); updateCopy(); }
  function queueEnsure() { if (queued) return; queued = true; requestAnimationFrame(() => { queued = false; ensureUi(); }); }
  function startSave(action) {
    const form = byId("kcCaptureForm");
    const source = byId("kcSaveDraft");
    if (!form || pendingSave || !source || source.disabled) return;
    if (!clean(form.elements.supplier.value) || !photoCount()) {
      const missingSupplier = !clean(form.elements.supplier.value);
      setText(byId("kcEditorMessage"), missingSupplier ? "糸商 / Supplierを選択または入力してください。" : "写真を1枚以上追加してください。");
      byId("kcEditorMessage")?.classList.add("error");
      if (missingSupplier) form.elements.supplier.focus();
      else byId("kcSimpleQuickPhoto")?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    pendingSave = action; savedResult = null; updateControls(); source.click();
  }
  document.addEventListener("kc:capture-opened", () => {
    ensureUi();
    const form = byId("kcCaptureForm");
    if (!clean(form.elements.record_id.value)) {
      const context = nextContext || (simpleMode() ? readSession() : null);
      if (context) { setField(form.elements.visit_context, clean(context.visitContext)); setField(form.elements.supplier, clean(context.supplier)); }
      if (nextContext) form.elements.supplier.focus({ preventScroll: true });
    }
    nextContext = null;
    document.body.classList.remove("kc-simple-show-details");
    updateControls();
  });
  document.addEventListener("kc:capture-saved", event => { if (pendingSave) savedResult = event.detail; });
  document.addEventListener("kc:capture-save-finished", () => {
    const action = pendingSave;
    const result = savedResult;
    pendingSave = null; savedResult = null;
    if (result) {
      if (action === "save-next") {
        rememberSession(null);
        nextContext = { supplier: "", visitContext: result.visitContext };
        byId("kcNewCapture")?.click();
      } else rememberSession(result);
    }
    updateControls();
  });
  document.addEventListener("click", event => {
    const button = event.target.closest?.("[data-simple-action]");
    if (!button || button.disabled) return;
    switch (button.dataset.simpleAction) {
      case "toggle-mode": {
        const enabled = !simpleMode();
        document.body.classList.toggle("kc-simple-capture-mode", enabled);
        document.body.classList.remove("kc-simple-show-details");
        try { localStorage.setItem(MODE_KEY, enabled ? "simple" : "full"); } catch (_error) {}
        ensureUi(); break;
      }
      case "history": document.body.classList.toggle("kc-simple-history-open"); updateControls(); break;
      case "details": document.body.classList.toggle("kc-simple-show-details"); updateControls(); break;
      case "save": case "save-next": startSave(button.dataset.simpleAction); break;
    }
  });
  document.addEventListener("change", queueEnsure);
  new MutationObserver(queueEnsure).observe(byId("app") || document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ["hidden", "disabled"] });
  if (preferredSimpleMode()) document.body.classList.add("kc-simple-capture-mode");
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", queueEnsure, { once: true }); else queueEnsure();
})();
