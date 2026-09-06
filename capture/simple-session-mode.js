(function knitCompassSimpleSessionMode() {
  "use strict";

  const BUILD = "2.1.45-simple-session.1";
  const SESSION_KEY = "kc_photo_capture_simple_supplier_session_v1";
  const MODE_KEY = "kc_photo_capture_simple_mode_v1";
  const MAX_SESSION_AGE_MS = 18 * 60 * 60 * 1000;

  let renderQueued = false;
  let pendingNext = false;
  let lastEditorHidden = true;

  function clean(value) {
    return String(value == null ? "" : value).trim();
  }

  function captureForm() {
    return document.getElementById("kcCaptureForm");
  }

  function editor() {
    return document.getElementById("kcEditor");
  }

  function isNewRecord(form) {
    return !clean(form?.elements?.record_id?.value);
  }

  function dispatchField(input, type) {
    if (!input) return;
    input.dispatchEvent(new Event(type, { bubbles: true }));
  }

  function setFieldValue(input, value) {
    if (!input || clean(input.value) === clean(value)) return;
    input.value = value;
    dispatchField(input, "input");
    dispatchField(input, "change");
  }

  function readSession() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const supplier = clean(parsed.supplier);
      const savedAt = Number(parsed.savedAt || 0);
      if (!supplier || !savedAt || Date.now() - savedAt > MAX_SESSION_AGE_MS) {
        localStorage.removeItem(SESSION_KEY);
        return null;
      }
      return {
        supplier,
        visitContext: clean(parsed.visitContext),
        sequence: Math.max(1, Number(parsed.sequence) || 1),
        startedAt: Number(parsed.startedAt || savedAt),
        savedAt,
        build: clean(parsed.build)
      };
    } catch (_error) {
      return null;
    }
  }

  function writeSessionFromForm(form, options = {}) {
    if (!form) return null;
    const supplier = clean(form.elements?.supplier?.value);
    if (!supplier) return null;
    const visitContext = clean(form.elements?.visit_context?.value);
    const previous = readSession();
    const sameSupplier = Boolean(previous && previous.supplier === supplier && previous.visitContext === visitContext);
    const sequence = options.sequence != null
      ? Math.max(1, Number(options.sequence) || 1)
      : (sameSupplier ? previous.sequence : 1);
    const next = {
      supplier,
      visitContext,
      sequence,
      startedAt: sameSupplier ? previous.startedAt : Date.now(),
      savedAt: Date.now(),
      build: BUILD
    };
    try {
      localStorage.setItem(SESSION_KEY, JSON.stringify(next));
      return next;
    } catch (_error) {
      return null;
    }
  }

  function clearSession() {
    try {
      localStorage.removeItem(SESSION_KEY);
    } catch (_error) {
      // Convenience state only. Capture data is untouched.
    }
  }

  function incrementSessionSequence() {
    const form = captureForm();
    const session = writeSessionFromForm(form);
    if (!session) return null;
    return writeSessionFromForm(form, { sequence: session.sequence + 1 });
  }

  function applySessionToNewRecord() {
    const form = captureForm();
    const currentEditor = editor();
    const session = readSession();
    if (!form || !currentEditor || currentEditor.hidden || !session || !isNewRecord(form)) return;

    const supplierInput = form.elements?.supplier;
    const visitInput = form.elements?.visit_context;
    if (visitInput && !clean(visitInput.value) && session.visitContext) {
      setFieldValue(visitInput, session.visitContext);
    }
    if (supplierInput && !clean(supplierInput.value)) {
      setFieldValue(supplierInput, session.supplier);
    }
  }

  function preferredSimpleMode() {
    const params = new URLSearchParams(location.search);
    if (params.get("full") === "1") return false;
    try {
      const stored = localStorage.getItem(MODE_KEY);
      return stored !== "full";
    } catch (_error) {
      return true;
    }
  }

  function setSimpleMode(enabled) {
    document.body.classList.toggle("kc-simple-capture-mode", enabled);
    if (!enabled) document.body.classList.remove("kc-simple-show-details", "kc-simple-history-open");
    try {
      localStorage.setItem(MODE_KEY, enabled ? "simple" : "full");
    } catch (_error) {
      // Preference only.
    }
    updateModeControls();
  }

  function simpleModeEnabled() {
    return document.body.classList.contains("kc-simple-capture-mode");
  }

  function detailsVisible() {
    return document.body.classList.contains("kc-simple-show-details");
  }

  function activePhotoCountFromUi() {
    const text = clean(document.getElementById("kcPhotoCount")?.textContent);
    const match = text.match(/^(\d+)/);
    return match ? Number(match[1]) : 0;
  }

  function buildModeToggle() {
    if (document.getElementById("kcSimpleModeToggle")) return;
    const host = document.querySelector(".kc-topbar .kc-session") || document.querySelector(".kc-topbar");
    if (!host) return;
    const button = document.createElement("button");
    button.type = "button";
    button.id = "kcSimpleModeToggle";
    button.className = "ghost kc-simple-mode-toggle";
    button.dataset.simpleAction = "toggle-mode";
    host.appendChild(button);
  }

  function buildHistoryToggle() {
    if (document.getElementById("kcSimpleHistoryToggle")) return;
    const actions = document.querySelector("#kcInbox .kc-primary-actions");
    if (!actions) return;
    const button = document.createElement("button");
    button.type = "button";
    button.id = "kcSimpleHistoryToggle";
    button.className = "secondary";
    button.dataset.simpleAction = "history";
    actions.appendChild(button);
  }

  function updateModeControls() {
    const toggle = document.getElementById("kcSimpleModeToggle");
    if (toggle) toggle.textContent = simpleModeEnabled() ? "通常画面" : "シンプル撮影";
    const history = document.getElementById("kcSimpleHistoryToggle");
    if (history) {
      history.textContent = document.body.classList.contains("kc-simple-history-open")
        ? "保存済みを閉じる"
        : "保存済みを見る";
    }
    document.querySelectorAll('[data-simple-action="details"]').forEach((button) => {
      button.textContent = detailsVisible() ? "詳細入力を閉じる" : "詳細入力";
    });
  }

  function markSimpleFields(form) {
    if (!form || form.dataset.kcSimpleFieldsMarked === "true") return;
    form.dataset.kcSimpleFieldsMarked = "true";

    const keepBasic = new Set(["entry_date", "visit_context", "supplier", "yarn_name"]);
    const keepMaterial = new Set(["yarn_count", "composition", "notes"]);

    const basic = document.getElementById("kcBasicTitle")?.closest(".kc-form-section");
    const photo = document.getElementById("kcPhotoTitle")?.closest(".kc-form-section");
    const material = document.getElementById("kcMaterialTitle")?.closest(".kc-form-section");
    const action = document.getElementById("kcActionTitle")?.closest(".kc-form-section");
    const research = document.getElementById("kcResearchTitle")?.closest(".kc-form-section");
    const details = form.querySelector(".kc-kc-details");

    basic?.classList.add("kc-simple-section-basic");
    photo?.classList.add("kc-simple-section-photo");
    material?.classList.add("kc-simple-section-material");
    action?.classList.add("kc-simple-hidden-section");
    research?.classList.add("kc-simple-hidden-section");
    details?.classList.add("kc-simple-hidden-section");

    basic?.querySelectorAll("label.kc-company-question").forEach((label) => {
      const control = label.querySelector("input[name], select[name], textarea[name]");
      if (control && !keepBasic.has(control.name)) label.classList.add("kc-simple-hidden-field");
    });

    material?.querySelectorAll("label.kc-company-question, fieldset.kc-company-question").forEach((block) => {
      const control = block.querySelector("input[name], select[name], textarea[name]");
      if (!control || !keepMaterial.has(control.name)) block.classList.add("kc-simple-hidden-field");
    });

    photo?.querySelector(".kc-primary-photo-slot")?.classList.add("kc-simple-photo-original");
    photo?.querySelector(".kc-photo-category-guide")?.classList.add("kc-simple-photo-original");
    photo?.querySelector(".kc-photo-grid")?.classList.add("kc-simple-photo-original");
    form.querySelector(".kc-policy")?.classList.add("kc-simple-hidden-section");
    form.querySelector(".kc-form-actions")?.classList.add("kc-simple-original-actions");
  }

  function buildSessionPanel(form) {
    if (!form || document.getElementById("kcSimpleSessionPanel")) return;
    const basic = document.getElementById("kcBasicTitle")?.closest(".kc-form-section");
    if (!basic) return;
    const panel = document.createElement("section");
    panel.id = "kcSimpleSessionPanel";
    panel.className = "kc-simple-session-panel";
    panel.innerHTML = `
      <div class="kc-simple-session-copy">
        <span class="kc-simple-kicker">メーカー連続撮影</span>
        <strong id="kcSimpleSessionTitle">メーカーを選択</strong>
        <span id="kcSimpleSessionSummary">メーカー名を一度入力すると、次の素材へ自動で引き継ぎます。</span>
      </div>
      <div class="kc-simple-session-badge" id="kcSimpleSequence">素材 01</div>
      <button type="button" class="secondary" data-simple-action="change-supplier">メーカー変更</button>
    `;
    basic.insertAdjacentElement("beforebegin", panel);
  }

  function buildQuickPhotoPanel(form) {
    if (!form || document.getElementById("kcSimpleQuickPhoto")) return;
    const photo = document.getElementById("kcPhotoTitle")?.closest(".kc-form-section");
    const heading = photo?.querySelector(".kc-section-heading");
    if (!photo || !heading) return;

    const panel = document.createElement("div");
    panel.id = "kcSimpleQuickPhoto";
    panel.className = "kc-simple-quick-photo";
    panel.innerHTML = `
      <div class="kc-simple-quick-photo-heading">
        <div>
          <span class="kc-simple-kicker">QUICK PHOTO</span>
          <strong>写真を連続追加</strong>
          <span>分類は後回し。まず撮影テンポを優先します。</span>
        </div>
        <span id="kcSimplePhotoCount" class="kc-simple-photo-count">0 / 10枚</span>
      </div>
      <div class="kc-simple-photo-actions">
        <label class="kc-simple-camera-button">撮影
          <input class="kc-visually-hidden-file" type="file" accept="image/*" capture="environment" data-photo-input="other" data-photo-source="camera">
        </label>
        <label class="kc-simple-library-button">写真からまとめて選択
          <input class="kc-visually-hidden-file" type="file" accept="image/*" multiple data-photo-input="other" data-photo-source="library">
        </label>
      </div>
      <div id="kcSimpleQuickPreview" class="kc-simple-quick-preview"><span>写真はまだありません</span></div>
      <button type="button" class="ghost kc-simple-details-inline" data-simple-action="details">分類別撮影・詳細入力</button>
    `;
    heading.insertAdjacentElement("afterend", panel);
  }

  function buildQuickActions(form) {
    if (!form || document.getElementById("kcSimpleActions")) return;
    const original = form.querySelector(".kc-form-actions");
    if (!original) return;
    const actions = document.createElement("div");
    actions.id = "kcSimpleActions";
    actions.className = "kc-simple-actions";
    actions.innerHTML = `
      <button type="button" class="kc-simple-next" data-simple-action="next">保存して次の素材</button>
      <button type="button" class="secondary" data-simple-action="finish">保存して終了</button>
      <button type="button" class="ghost" data-simple-action="details">詳細入力</button>
    `;
    original.insertAdjacentElement("beforebegin", actions);
  }

  function updateSessionPanel() {
    const form = captureForm();
    const panel = document.getElementById("kcSimpleSessionPanel");
    if (!form || !panel) return;
    const session = readSession();
    const currentSupplier = clean(form.elements?.supplier?.value);
    const currentVisit = clean(form.elements?.visit_context?.value);
    const active = currentSupplier || session?.supplier || "";
    const visit = currentVisit || session?.visitContext || "";
    const sequence = session?.sequence || 1;
    const title = document.getElementById("kcSimpleSessionTitle");
    const summary = document.getElementById("kcSimpleSessionSummary");
    const sequenceNode = document.getElementById("kcSimpleSequence");

    if (title) title.textContent = active ? `${active} 固定中` : "メーカーを選択";
    if (summary) {
      summary.textContent = active
        ? `${visit ? `${visit} / ` : ""}このメーカーのまま素材を続けて登録できます。`
        : "メーカー名を一度入力すると、次の素材へ自動で引き継ぎます。";
    }
    if (sequenceNode) sequenceNode.textContent = `素材 ${String(sequence).padStart(2, "0")}`;
    panel.dataset.active = active ? "true" : "false";
  }

  function updateQuickPhotoPreview() {
    const count = document.getElementById("kcPhotoCount");
    const mirrorCount = document.getElementById("kcSimplePhotoCount");
    if (count && mirrorCount) mirrorCount.textContent = clean(count.textContent) || "0 / 10枚";

    const source = document.querySelector('[data-photo-preview="other"]');
    const target = document.getElementById("kcSimpleQuickPreview");
    if (!source || !target) return;
    const images = [...source.querySelectorAll("img")].slice(-6);
    if (!images.length) {
      target.dataset.signature = "";
      target.innerHTML = "<span>写真はまだありません</span>";
      return;
    }
    const signature = images.map((image) => image.src).join("|");
    if (target.dataset.signature === signature) return;
    target.dataset.signature = signature;
    target.innerHTML = "";
    images.forEach((image) => {
      const clone = document.createElement("img");
      clone.src = image.src;
      clone.alt = "撮影済み写真";
      target.appendChild(clone);
    });
  }

  function updateQuickActionState() {
    const source = document.getElementById("kcSaveDraft");
    const next = document.querySelector('[data-simple-action="next"]');
    const finish = document.querySelector('[data-simple-action="finish"]');
    const disabled = Boolean(source?.disabled);
    if (next) next.disabled = disabled;
    if (finish) finish.disabled = disabled;
  }

  function updateSimpleCopy() {
    const heading = document.querySelector(".kc-brand h1");
    const lead = document.querySelector(".kc-brand .kc-lead");
    if (heading && !heading.dataset.kcSimpleOriginal) heading.dataset.kcSimpleOriginal = heading.textContent;
    if (lead && !lead.dataset.kcSimpleOriginal) lead.dataset.kcSimpleOriginal = lead.textContent;
    if (simpleModeEnabled()) {
      if (heading) heading.textContent = "Photo Capture";
      if (lead) lead.textContent = "メーカーを一度選び、素材ごとに写真をテンポよく連続撮影します。詳細項目は必要な時だけ開けます。";
    } else {
      if (heading?.dataset.kcSimpleOriginal) heading.textContent = heading.dataset.kcSimpleOriginal;
      if (lead?.dataset.kcSimpleOriginal) lead.textContent = lead.dataset.kcSimpleOriginal;
    }
  }

  function ensureUi() {
    buildModeToggle();
    buildHistoryToggle();
    const form = captureForm();
    if (form) {
      markSimpleFields(form);
      buildSessionPanel(form);
      buildQuickPhotoPanel(form);
      buildQuickActions(form);
      applySessionToNewRecord();
    }
    updateModeControls();
    updateSessionPanel();
    updateQuickPhotoPreview();
    updateQuickActionState();
    updateSimpleCopy();

    const currentEditor = editor();
    if (currentEditor) {
      const hidden = currentEditor.hidden;
      if (pendingNext && hidden && !lastEditorHidden) {
        pendingNext = false;
        incrementSessionSequence();
        window.setTimeout(() => document.getElementById("kcNewCapture")?.click(), 80);
      }
      lastEditorHidden = hidden;
    }
  }

  function queueEnsure() {
    if (renderQueued) return;
    renderQueued = true;
    window.requestAnimationFrame(() => {
      renderQueued = false;
      ensureUi();
    });
  }

  function showFormMessage(text, isError = false) {
    const target = document.getElementById("kcEditorMessage");
    if (!target) return;
    target.textContent = text;
    target.classList.toggle("error", isError);
  }

  function startSave(nextAfterSave) {
    const form = captureForm();
    if (!form) return;
    const supplier = clean(form.elements?.supplier?.value);
    if (!supplier && nextAfterSave) {
      showFormMessage("連続撮影では、最初にメーカー / Supplierを入力してください。", true);
      form.elements?.supplier?.focus();
      return;
    }
    if (activePhotoCountFromUi() < 1) {
      showFormMessage("この素材の写真を1枚以上追加してから保存してください。", true);
      document.querySelector(".kc-simple-camera-button")?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    if (supplier) writeSessionFromForm(form);
    pendingNext = Boolean(nextAfterSave);
    document.getElementById("kcSaveDraft")?.click();
  }

  document.addEventListener("click", (event) => {
    const action = event.target.closest?.("[data-simple-action]");
    if (!action) return;
    const name = action.dataset.simpleAction;

    if (name === "toggle-mode") {
      setSimpleMode(!simpleModeEnabled());
      queueEnsure();
      return;
    }
    if (name === "history") {
      document.body.classList.toggle("kc-simple-history-open");
      updateModeControls();
      return;
    }
    if (name === "details") {
      document.body.classList.toggle("kc-simple-show-details");
      updateModeControls();
      return;
    }
    if (name === "next") {
      startSave(true);
      return;
    }
    if (name === "finish") {
      startSave(false);
      return;
    }
    if (name === "change-supplier") {
      clearSession();
      const form = captureForm();
      if (form && isNewRecord(form)) {
        setFieldValue(form.elements?.supplier, "");
        setFieldValue(form.elements?.visit_context, "");
        form.elements?.supplier?.focus();
      }
      updateSessionPanel();
    }
  }, true);

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.form || target.form.id !== "kcCaptureForm") return;
    if (!["supplier", "visit_context"].includes(target.name)) return;
    if (clean(target.form.elements?.supplier?.value)) writeSessionFromForm(target.form);
    updateSessionPanel();
  });

  document.addEventListener("change", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) && !(target instanceof HTMLSelectElement)) return;
    if (!target.form || target.form.id !== "kcCaptureForm") return;
    if (["supplier", "visit_context"].includes(target.name) && clean(target.form.elements?.supplier?.value)) {
      writeSessionFromForm(target.form);
      updateSessionPanel();
    }
    queueEnsure();
  });

  const root = document.getElementById("app") || document.documentElement;
  const observer = new MutationObserver(queueEnsure);
  observer.observe(root, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ["hidden", "disabled", "class"]
  });

  if (preferredSimpleMode()) document.body.classList.add("kc-simple-capture-mode");

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", queueEnsure, { once: true });
  } else {
    queueEnsure();
  }
})();
