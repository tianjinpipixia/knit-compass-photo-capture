(function knitCompassIndependentPhotoCaptureV11Candidate() {
  "use strict";

  const CONTRACT = Object.freeze({
    application: "Knit Compass Independent Photo Capture",
    version: "2.1.43-independent.1",
    feature_version: "COMPANY_MATERIAL_PHOTO_COMPATIBILITY",
    implementation_scope: "OWNER_DEVICE_DRAFT_WITH_PORTABLE_HANDOFF",
    database_name: "kc_independent_photo_capture_v1_0",
    photo_store: "photos",
    event_store: "events",
    audit_store: "audit",
    authentication_realm: "KNIT_COMPASS_DEVICE_LOCAL",
    initial_state: "DRAFT",
    allowed_states: ["DRAFT", "REVIEW", "CONFIRMED", "ARCHIVED"],
    history_policy: "APPEND_ONLY",
    automatic_sync: "OFF_PORTABLE_ZIP_ONLY",
    automatic_publish: "OFF",
    production_release: "HOLD",
    external_network_calls: "OFF",
    image_orientation_normalization: "ON",
    device_save: "USER_INITIATED_DOWNLOAD",
    portable_export: "USER_SELECTED_RECORD_CSV_PHOTO_ZIP",
    portable_export_schema: "KC_PORTABLE_PHOTO_EXPORT_V1",
    company_adapter_schema: "COMPANY_PHOTO_CAPTURE_CURRENT_UI_SUBSET_V2",
    company_spreadsheet_payload_schema: "COMPANY_MATERIAL_PHOTO_PAYLOAD_CURRENT",
    database_compatibility: "V1_0_SHARED"
  });

  const BUILD_INFO = Object.freeze({
    version: "2.1.43 独立版",
    updated_at: "2026-08-26T07:41:09+08:00",
    updated_label: "2026-08-26 07:41 CST"
  });

  const COMPANY_IMPORT_FILE = "Company_PhotoCapture_External_Import.csv";
  const SESSION_KEY = "kc_session_v1";

  const STORES = Object.freeze({
    accounts: "accounts",
    events: CONTRACT.event_store,
    audit: CONTRACT.audit_store,
    photos: CONTRACT.photo_store,
    masters: "masters"
  });

  const MASTER_VALUES = Object.freeze({
    supplier: ["Sample Supplier A", "Sample Supplier B", "Sample Mill C"],
    yarn_name: ["Sample Air Yarn", "Sample Compact Yarn", "Sample Stretch Yarn"],
    abbreviation: ["SAY", "SCY", "SSY"],
    material: ["Sample Cotton", "Sample Recycled Polyester", "Sample Nylon"],
    processing_method: ["Compact", "Ring", "Siro", "MVS", "DTY", "FDY", "Air Covered"]
  });

  const EXHIBITION_SUPPLIER_MASTER = window.KC_EXHIBITION_SUPPLIER_MASTER_V1 || Object.freeze({ events: [] });
  const EXHIBITION_EVENTS = Object.freeze(Array.isArray(EXHIBITION_SUPPLIER_MASTER.events)
    ? [...EXHIBITION_SUPPLIER_MASTER.events]
    : []);
  const ACQUISITION_SOURCE_OPTIONS = Object.freeze([
    ...EXHIBITION_EVENTS.map((event) => event.label),
    "展示会",
    "訪問先",
    "商談先",
    "資料受領",
    "その他"
  ]);
  const SEASONS = ["春夏", "秋冬", "シーズンレス"];
  const SPINNING_METHODS = Object.freeze([
    "リング精紡",
    "コンパクト精紡",
    "サイロ精紡",
    "サイロコンパクト精紡",
    "MVS・渦流精紡",
    "ローター・オープンエンド精紡",
    "エアジェット精紡",
    "その他"
  ]);
  const SPINNING_METHOD_LABELS = Object.freeze({
    "リング精紡": "リング精紡（Ring）",
    "コンパクト精紡": "コンパクト精紡（Compact）",
    "サイロ精紡": "サイロ精紡（Siro）",
    "サイロコンパクト精紡": "サイロコンパクト精紡（Siro Compact）",
    "MVS・渦流精紡": "MVS・渦流精紡（Vortex）",
    "ローター・オープンエンド精紡": "OE・ローター精紡（Open End / Rotor）",
    "エアジェット精紡": "エアジェット精紡（Air Jet）",
    "その他": "その他"
  });
  const LEGACY_SPINNING_METHOD_LABELS = Object.freeze({
    Ring: "リング精紡",
    Compact: "コンパクト精紡",
    Siro: "サイロ精紡",
    "Compact Siro": "サイロコンパクト精紡",
    "Siro Compact": "サイロコンパクト精紡",
    MVS: "MVS・渦流精紡",
    Vortex: "MVS・渦流精紡",
    "Open End": "ローター・オープンエンド精紡",
    OE: "ローター・オープンエンド精紡",
    Rotor: "ローター・オープンエンド精紡",
    "Air Jet": "エアジェット精紡",
    リング: "リング精紡",
    コンパクト: "コンパクト精紡",
    サイロ: "サイロ精紡",
    サイロコンパクト: "サイロコンパクト精紡",
    渦流: "MVS・渦流精紡",
    ローター: "ローター・オープンエンド精紡",
    オープンエンド: "ローター・オープンエンド精紡",
    エアジェット: "エアジェット精紡"
  });
  const FILAMENT_TYPES = Object.freeze(["FDY", "DTY", "ATY", "POY", "その他"]);
  const FILAMENT_TYPE_LABELS = Object.freeze({
    FDY: "FDY（完全延伸糸）",
    DTY: "DTY（延伸仮撚加工糸）",
    ATY: "ATY（空気加工糸）",
    POY: "POY（部分配向糸）",
    その他: "その他"
  });
  const LEGACY_FILAMENT_TYPE_LABELS = Object.freeze({
    完全延伸糸: "FDY",
    延伸仮撚加工糸: "DTY",
    空気加工糸: "ATY",
    部分配向糸: "POY",
    半延伸糸: "POY"
  });
  const COMPOSITE_STRUCTURES = Object.freeze(["不明", "Core Spun", "Covered Yarn", "SCY", "DCY", "SiroFil", "Composite", "Twisted", "Fancy Yarn", "その他"]);
  const YARN_STRUCTURES = Object.freeze(["未確認", "単糸", "合撚", "交撚", "コアスパン", "カバリング", "ファンシー", "その他"]);
  const PRICE_CURRENCIES = Object.freeze(["CNY", "JPY", "USD", "EUR", "KRW", "HKD", "未確認"]);
  const PRICE_UNITS = Object.freeze(["kg", "lb", "コーン", "本", "未確認"]);
  const GAUGES = Object.freeze(["未確認", "3G", "5G", "7G", "8G", "9G", "10G", "12G", "14G", "16G", "18G", "その他"]);
  const KNIT_STRUCTURES = Object.freeze(["天竺", "総針", "リブ", "スムース", "ミラノリブ", "ガーター", "鹿の子", "片畦", "両畦", "ポンチ", "接結", "ジャカード", "インターシャ", "ケーブル", "透かし柄", "メッシュ", "パイル", "その他", "未確認"]);
  const KNITTING_TECHNIQUES = Object.freeze(["プレーティング", "引き揃え", "インレイ", "接結", "成型（ホールガーメント等）", "その他"]);
  const BOOK_AVAILABILITY_VALUES = Object.freeze(["あり", "なし", "未確認"]);
  const BOOK_AVAILABILITY_LABELS = Object.freeze({
    あり: "掲載あり",
    なし: "掲載なし",
    未確認: "確認中"
  });
  const SAMPLE_STATUS_VALUES = Object.freeze(["現物糸あり", "BOOK帳あり（カラーカード含む）", "スワッチあり", "カタログあり"]);
  const BOOK_SAMPLE_STATUS = "BOOK帳あり（カラーカード含む）";
  const TACTILE_FEELINGS = Object.freeze([
    "柔らかい", "ドライ", "清涼", "膨らみ", "ハリ", "落ち感", "光沢", "麻見え", "毛羽", "スポンディッシュ"
  ]);
  const ATTENTION_RATINGS = Object.freeze([
    "★（参考）", "★★（気になる）", "★★★（すぐ見てほしい）"
  ]);
  const DEVELOPMENT_ACTIONS = Object.freeze(["サンプル取り寄せ", "顧客提案", "開発候補", "継続ウォッチ"]);
  const MAX_PHOTOS_PER_RECORD = 10;
  const MAX_PORTABLE_ZIP_BYTES = 512 * 1024 * 1024;
  const PHOTO_TYPES = Object.freeze([
    { key: "specification", label: "品質表示・規格", description: "中国語など、読めない表示でもそのまま撮影してください" },
    { key: "cover", label: "表紙・全体", description: "糸帳やカタログの表紙、資料全体" },
    { key: "material", label: "糸・素材本体", description: "糸、糸カード、素材そのもの" },
    { key: "fabric", label: "編地・質感", description: "編地、スワッチ、風合いのアップ" },
    { key: "color", label: "色見本（カラーBOOK）", description: "カラーBOOKや色展開が分かる写真" },
    { key: "wechat", label: "WeChat・連絡記録", description: "糸商とのWeChat会話、仕様確認、回答のスクリーンショット" },
    { key: "other", label: "その他", description: "上記に当てはまらない補足写真" }
  ]);
  const CAPTURE_PHOTO_TYPES = Object.freeze([
    PHOTO_TYPES[0],
    ...PHOTO_TYPES.slice(1, 5),
    PHOTO_TYPES[6],
    PHOTO_TYPES[5]
  ]);
  const LEGACY_PHOTO_TYPES = Object.freeze([
    { key: "product", label: "商品写真（旧分類）", order: 0 },
    { key: "yarn", label: "糸写真（旧分類）", order: 1 },
    { key: "yarn_book", label: "糸帳写真（旧分類）", order: 5 }
  ]);
  const ALL_PHOTO_TYPES = Object.freeze([...PHOTO_TYPES, ...LEGACY_PHOTO_TYPES]);
  const COMPANY_IMPORT_HEADERS = Object.freeze([
    "capture_date", "operator_name", "department", "document_type", "visit_context", "supplier", "yarn_name",
    "season", "factory", "importance", "yarn_count_spec", "yarn_structure", "composition", "price", "currency",
    "gauge", "knit_structure", "tactile_feeling", "functional_fiber_usage", "memo", "book_request", "fabric_request",
    "arrangement_memo", "research_request", "photo_1", "photo_2", "photo_3", "photo_4", "photo_5", "photo_6",
    "photo_7", "photo_8", "photo_9", "photo_10"
  ]);

  const app = document.getElementById("app");
  const state = {
    db: null,
    session: null,
    events: [],
    latestRecords: [],
    masters: MASTER_VALUES,
    editingRecordId: "",
    existingPhotoRefs: [],
    pendingFiles: new Map(),
    removedPhotoIds: new Set(),
    objectUrls: new Set(),
    processingPhotos: new Set(),
    exportingRecords: new Set(),
    isPortableImporting: false,
    isSaving: false,
    isOnline: typeof navigator === "undefined" ? true : navigator.onLine !== false,
    saveDestination: "LOCAL",
    companyFactories: [],
    companyFactoriesLoaded: false,
    filters: { query: "", supplier: "", yarnName: "", abbreviation: "", season: "" }
  };

  function gaugeToken(value) {
    const raw = clean(value);
    if (!raw) return "";
    if (["未確認", "その他"].includes(raw)) return raw;
    const matched = raw.toUpperCase().match(/(\d+(?:\.\d+)?)\s*(?:G|GG)?/);
    return matched ? `${Number(matched[1])}G` : "";
  }

  function gaugeRange(minValue, maxValue, legacyValue = "") {
    let min = gaugeToken(minValue);
    let max = gaugeToken(maxValue);
    const legacy = clean(legacyValue);
    if (!min && !max && legacy) {
      const matches = [...legacy.toUpperCase().matchAll(/(\d+(?:\.\d+)?)\s*(?:G|GG)/g)]
        .map((match) => `${Number(match[1])}G`);
      if (matches.length) {
        min = matches[0];
        max = matches[matches.length - 1];
      } else if (["未確認", "その他"].includes(legacy)) {
        min = legacy;
        max = legacy;
      }
    }
    if (!min && max) min = max;
    if (min && !max) max = min;
    const numericMin = Number.parseFloat(min);
    const numericMax = Number.parseFloat(max);
    if (Number.isFinite(numericMin) && Number.isFinite(numericMax) && numericMin > numericMax) {
      [min, max] = [max, min];
    }
    let label = legacy;
    if (min && max) {
      label = min === max ? min : `${min}〜${max}`;
    }
    return { min, max, label };
  }

  function normalizeKnittingEndCount(value) {
    const raw = clean(value).normalize("NFKC");
    if (!raw) return "";
    const multiplied = raw.match(/(?:×|x)\s*(\d{1,2})/i);
    const matched = multiplied || raw.match(/^(\d{1,2})(?:\s*本(?:取り)?)?$/i);
    if (!matched) return "";
    const count = Number(matched[1]);
    return Number.isInteger(count) && count >= 1 && count <= 20 ? String(count) : "";
  }

  function knittingSpecificationLabel(gauge, knittingEndCount) {
    const gaugeLabel = clean(gauge);
    const endCount = normalizeKnittingEndCount(knittingEndCount);
    if (gaugeLabel && endCount) return `${gaugeLabel} × ${endCount}本取り`;
    if (gaugeLabel) return gaugeLabel;
    return endCount ? `${endCount}本取り` : "";
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function clean(value) {
    return String(value ?? "").trim();
  }

  function normalizedLookup(value) {
    return clean(value).normalize("NFKC").toLocaleLowerCase();
  }

  function exhibitionForVisitContext(value) {
    const lookup = normalizedLookup(value);
    if (!lookup) return null;
    return EXHIBITION_EVENTS.find((event) => [
      event.label,
      ...(Array.isArray(event.aliases) ? event.aliases : [])
    ].some((candidate) => normalizedLookup(candidate) === lookup)) || null;
  }

  function exhibitionSupplierCandidates(event) {
    return (Array.isArray(event?.exhibitors) ? event.exhibitors : [])
      .filter((exhibitor) => exhibitor.supplier_candidate !== false);
  }

  function supplierRecordForEvent(event, value) {
    const lookup = normalizedLookup(value);
    if (!event || !lookup) return null;
    return exhibitionSupplierCandidates(event).find((supplier) => [
      supplier.name_en,
      supplier.name_zh,
      supplier.display_name
    ].some((candidate) => normalizedLookup(candidate) === lookup)) || null;
  }

  function documentTypeForEditor(value) {
    return ({ "糸カード": "カラーBOOK", "編地": "編地・スワッチ", "製品": "製品サンプル" })[clean(value)] || clean(value);
  }

  function seasonsForEditor(values) {
    const mapped = (values || []).map((value) => ({
      Spring: "春夏", Summer: "春夏", Autumn: "秋冬", Winter: "秋冬",
      "All Season": "シーズンレス", "2027SS": "春夏", "2027AW": "秋冬", "2028SS": "春夏"
    })[value] || value);
    return [...new Set(mapped)];
  }

  function attentionRatingForEditor(value, priority) {
    if (ATTENTION_RATINGS.includes(clean(value))) return clean(value);
    if (["★★★★★", "★★★★☆"].includes(clean(value)) || priority === "URGENT") return "★★★（すぐ見てほしい）";
    if (["★★★☆☆", "★★☆☆☆"].includes(clean(value)) || priority === "HIGH") return "★★（気になる）";
    return "★（参考）";
  }

  function priorityFromAttentionRating(value) {
    if (["★★★（すぐ見てほしい）", "★★★★★", "★★★★☆"].includes(value)) return "URGENT";
    if (["★★（気になる）", "★★★☆☆", "★★☆☆☆"].includes(value)) return "HIGH";
    return "NORMAL";
  }

  function companyChoiceForEditor(value, choices) {
    const current = clean(value);
    if (!current) return { value: "不明", other: "" };
    if (choices.includes(current)) return { value: current, other: "" };
    return { value: "その他", other: current };
  }

  function canonicalSpinningMethod(value) {
    const raw = clean(value);
    if (!raw || ["UNKNOWN", "NOT AVAILABLE"].includes(raw.toUpperCase()) || ["不明", "未選択", "未確認"].includes(raw)) return "";
    return LEGACY_SPINNING_METHOD_LABELS[raw] || raw;
  }

  function spinningMethodChoiceForEditor(value) {
    const canonical = canonicalSpinningMethod(value);
    if (!canonical) return { value: "", other: "" };
    if (SPINNING_METHODS.includes(canonical)) return { value: canonical, other: "" };
    return { value: "その他", other: clean(value) };
  }

  function canonicalFilamentType(value) {
    const raw = clean(value);
    if (!raw || ["UNKNOWN", "NOT AVAILABLE"].includes(raw.toUpperCase()) || ["不明", "未選択", "未確認"].includes(raw)) return "";
    const upper = raw.toUpperCase();
    if (["FDY", "DTY", "ATY", "POY"].includes(upper)) return upper;
    return LEGACY_FILAMENT_TYPE_LABELS[raw] || raw;
  }

  function filamentTypeChoiceForEditor(value) {
    const canonical = canonicalFilamentType(value);
    if (!canonical) return { value: "", other: "" };
    if (FILAMENT_TYPES.includes(canonical)) return { value: canonical, other: "" };
    return { value: "その他", other: clean(value) };
  }

  function tactileFeelingsForEditor(values) {
    const aliases = {
      "柔らかい・ソフト感": "柔らかい",
      "ドライタッチ": "ドライ",
      "さらっと感": "ドライ",
      "清涼感": "清涼",
      "接触冷感": "清涼",
      "ふくらみ感": "膨らみ",
      "もちふわ感": "膨らみ",
      "ハリ感": "ハリ",
      "ドレープ感": "落ち感",
      "毛羽感": "毛羽"
    };
    const selected = [];
    const legacy = [];
    (values || []).forEach((value) => {
      const mapped = aliases[value] || value;
      if (TACTILE_FEELINGS.includes(mapped)) selected.push(mapped);
      else legacy.push(value);
    });
    return { selected: [...new Set(selected)], legacy: [...new Set(legacy)] };
  }

  function parseStringArray(value) {
    try {
      const parsed = JSON.parse(clean(value) || "[]");
      return Array.isArray(parsed) ? parsed.map(clean).filter(Boolean) : [];
    } catch {
      return [];
    }
  }

  function normalizedFactoryName(value) {
    return clean(value).normalize("NFKC").toLocaleLowerCase("ja-JP").replace(/[・･]/g, " ").replace(/\s+/g, " ").trim();
  }

  function photoTypeDefinition(type) {
    return ALL_PHOTO_TYPES.find((item) => item.key === type) || { key: type || "other", label: "写真", order: 99 };
  }

  function photoCategoryOrder(type) {
    const currentIndex = PHOTO_TYPES.findIndex((item) => item.key === type);
    if (currentIndex >= 0) return currentIndex * 10;
    const legacy = LEGACY_PHOTO_TYPES.find((item) => item.key === type);
    return legacy ? legacy.order * 10 + 5 : 999;
  }

  function displayCategoryForType(type) {
    return ({ product: "cover", yarn: "material", yarn_book: "other" })[type] || type;
  }

  function sortPhotoEntries(entries) {
    return [...(entries || [])].sort((left, right) => {
      const typeDifference = photoCategoryOrder(left.record?.type || left.type) - photoCategoryOrder(right.record?.type || right.type);
      if (typeDifference) return typeDifference;
      const leftTime = left.record?.capturedAt || left.capturedAt || "";
      const rightTime = right.record?.capturedAt || right.capturedAt || "";
      return String(leftTime).localeCompare(String(rightTime)) || String(left.record?.photoId || left.photoId || "").localeCompare(String(right.record?.photoId || right.photoId || ""));
    });
  }

  function groupPhotoPaths(photoItems) {
    const paths = {};
    sortPhotoEntries(photoItems).forEach((item) => {
      const type = item.record?.type || item.type || "other";
      if (!paths[type]) paths[type] = [];
      if (item.path) paths[type].push(item.path);
    });
    return paths;
  }

  function activeExistingPhotoRefs() {
    const replacedPhotoIds = new Set([...state.pendingFiles.values()].map((entry) => entry.replacesPhotoId).filter(Boolean));
    return state.existingPhotoRefs.filter((ref) => !state.removedPhotoIds.has(ref.photoId) && !replacedPhotoIds.has(ref.photoId));
  }

  function activePhotoCount() {
    return activeExistingPhotoRefs().length + state.pendingFiles.size;
  }

  function createId(prefix) {
    return `${prefix}-${crypto.randomUUID()}`;
  }

  function isoNow() {
    return new Date().toISOString();
  }

  function formatDate(value) {
    if (!value) return "—";
    return new Intl.DateTimeFormat("ja-JP", {
      year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit"
    }).format(new Date(value));
  }

  function formatJstDate(value) {
    const parts = new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Tokyo", year: "numeric", month: "2-digit", day: "2-digit"
    }).formatToParts(new Date(value));
    const byType = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return `${byType.year}-${byType.month}-${byType.day}`;
  }

  function todayJst() {
    return formatJstDate(new Date().toISOString());
  }

  function syncCompatibilityDetailVisibility() {
    const form = document.getElementById("kcCaptureForm");
    if (!form) return;
    const functionalWrap = document.getElementById("kcFunctionalFiberDetailWrap");
    const sustainableWrap = document.getElementById("kcSustainableFiberDetailWrap");
    const yarnOtherWrap = document.getElementById("kcYarnStructureOtherWrap");
    if (functionalWrap) functionalWrap.hidden = clean(form.elements.functional_fiber_usage.value) !== "あり";
    if (sustainableWrap) sustainableWrap.hidden = clean(form.elements.sustainable_fiber_usage.value) !== "あり";
    if (yarnOtherWrap) yarnOtherWrap.hidden = clean(form.elements.yarn_structure.value) !== "その他";
  }

  function requestPromise(request) {
    return new Promise((resolve, reject) => {
      request.addEventListener("success", () => resolve(request.result), { once: true });
      request.addEventListener("error", () => reject(request.error || new Error("SANDBOX_DB_REQUEST_FAILED")), { once: true });
    });
  }

  function transactionPromise(transaction) {
    return new Promise((resolve, reject) => {
      transaction.addEventListener("complete", () => resolve(), { once: true });
      transaction.addEventListener("abort", () => reject(transaction.error || new Error("SANDBOX_DB_TRANSACTION_ABORTED")), { once: true });
      transaction.addEventListener("error", () => reject(transaction.error || new Error("SANDBOX_DB_TRANSACTION_FAILED")), { once: true });
    });
  }

  function connectDatabase(version) {
    return new Promise((resolve, reject) => {
      const request = version ? indexedDB.open(CONTRACT.database_name, version) : indexedDB.open(CONTRACT.database_name);
      request.addEventListener("upgradeneeded", () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORES.accounts)) {
          db.createObjectStore(STORES.accounts, { keyPath: "accountId" });
        }
        if (!db.objectStoreNames.contains(STORES.events)) {
          const store = db.createObjectStore(STORES.events, { keyPath: "eventId" });
          store.createIndex("recordId", "recordId", { unique: false });
          store.createIndex("createdAt", "createdAt", { unique: false });
        }
        if (!db.objectStoreNames.contains(STORES.audit)) {
          const store = db.createObjectStore(STORES.audit, { keyPath: "auditId" });
          store.createIndex("recordId", "recordId", { unique: false });
          store.createIndex("createdAt", "createdAt", { unique: false });
        }
        if (!db.objectStoreNames.contains(STORES.photos)) {
          const store = db.createObjectStore(STORES.photos, { keyPath: "photoId" });
          store.createIndex("recordId", "recordId", { unique: false });
        }
        if (!db.objectStoreNames.contains(STORES.masters)) {
          db.createObjectStore(STORES.masters, { keyPath: "masterType" });
        }
      });
      request.addEventListener("success", () => resolve(request.result), { once: true });
      request.addEventListener("error", () => reject(request.error || new Error("SANDBOX_DB_OPEN_FAILED")), { once: true });
      request.addEventListener("blocked", () => reject(new Error("SANDBOX_DB_UPGRADE_BLOCKED")), { once: true });
    });
  }

  async function openDatabase() {
    let database = await connectDatabase();
    const requiredStores = Object.values(STORES);
    const missingStores = requiredStores.filter((name) => !database.objectStoreNames.contains(name));
    if (!missingStores.length) return database;
    const nextVersion = database.version + 1;
    database.close();
    database = await connectDatabase(nextVersion);
    return database;
  }

  async function passwordHash(password, salt, iterations = 180000) {
    const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveBits"]);
    const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt, iterations }, key, 256);
    return [...new Uint8Array(bits)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function generatedAccountId() {
    return `kc-owner-${createId("DEVICE").replace(/[^a-z0-9]/gi, "").slice(-16).toLowerCase()}`;
  }

  function withStartupTimeout(promise, timeoutMs, errorCode) {
    let timer;
    return Promise.race([
      promise,
      new Promise((_, reject) => {
        timer = window.setTimeout(() => reject(new Error(errorCode)), timeoutMs);
      })
    ]).finally(() => window.clearTimeout(timer));
  }

  async function seedIndependentMasters() {
    const readTx = state.db.transaction(STORES.masters, "readonly");
    const existing = await requestPromise(readTx.objectStore(STORES.masters).get("supplier"));
    await transactionPromise(readTx);
    if (existing) return;
    const writeTx = state.db.transaction(STORES.masters, "readwrite");
    Object.entries(MASTER_VALUES).forEach(([masterType, values]) => {
      writeTx.objectStore(STORES.masters).add({
        masterType,
        values: [...values],
        source: "SYNTHETIC_INDEPENDENT_MASTER",
        createdAt: isoNow()
      });
    });
    await transactionPromise(writeTx);
  }

  async function readMasters() {
    const tx = state.db.transaction(STORES.masters, "readonly");
    const rows = await requestPromise(tx.objectStore(STORES.masters).getAll());
    await transactionPromise(tx);
    state.masters = rows.reduce((result, row) => {
      result[row.masterType] = Array.isArray(row.values) ? row.values : [];
      return result;
    }, {});
  }

  async function getAll(storeName) {
    const tx = state.db.transaction(storeName, "readonly");
    const rows = await requestPromise(tx.objectStore(storeName).getAll());
    await transactionPromise(tx);
    return rows;
  }

  async function getOne(storeName, key) {
    const tx = state.db.transaction(storeName, "readonly");
    const row = await requestPromise(tx.objectStore(storeName).get(key));
    await transactionPromise(tx);
    return row;
  }

  async function snapshotHash(snapshot) {
    const bytes = new TextEncoder().encode(JSON.stringify(snapshot));
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  async function sha256Hex(bytes) {
    const source = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    const digest = await crypto.subtle.digest("SHA-256", source);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  function crc32(bytes) {
    let crc = 0xffffffff;
    for (const byte of bytes) {
      crc ^= byte;
      for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ (0xedb88320 & -(crc & 1));
    }
    return (crc ^ 0xffffffff) >>> 0;
  }

  function zipDateTime(value) {
    const date = value instanceof Date ? value : new Date(value);
    const year = Math.max(1980, date.getFullYear());
    return {
      time: (date.getHours() << 11) | (date.getMinutes() << 5) | Math.floor(date.getSeconds() / 2),
      date: ((year - 1980) << 9) | ((date.getMonth() + 1) << 5) | date.getDate()
    };
  }

  function zipHeader(size) {
    const bytes = new Uint8Array(size);
    return { bytes, view: new DataView(bytes.buffer) };
  }

  function buildStoredZip(entries, modifiedAt = new Date()) {
    const encoder = new TextEncoder();
    const parts = [];
    const directory = [];
    const dos = zipDateTime(modifiedAt);
    let offset = 0;

    entries.forEach((entry) => {
      const name = encoder.encode(entry.path);
      const data = entry.bytes instanceof Uint8Array ? entry.bytes : new Uint8Array(entry.bytes);
      const checksum = crc32(data);
      const local = zipHeader(30);
      local.view.setUint32(0, 0x04034b50, true);
      local.view.setUint16(4, 20, true);
      local.view.setUint16(6, 0x0800, true);
      local.view.setUint16(8, 0, true);
      local.view.setUint16(10, dos.time, true);
      local.view.setUint16(12, dos.date, true);
      local.view.setUint32(14, checksum, true);
      local.view.setUint32(18, data.byteLength, true);
      local.view.setUint32(22, data.byteLength, true);
      local.view.setUint16(26, name.byteLength, true);
      local.view.setUint16(28, 0, true);
      parts.push(local.bytes, name, data);

      const central = zipHeader(46);
      central.view.setUint32(0, 0x02014b50, true);
      central.view.setUint16(4, 20, true);
      central.view.setUint16(6, 20, true);
      central.view.setUint16(8, 0x0800, true);
      central.view.setUint16(10, 0, true);
      central.view.setUint16(12, dos.time, true);
      central.view.setUint16(14, dos.date, true);
      central.view.setUint32(16, checksum, true);
      central.view.setUint32(20, data.byteLength, true);
      central.view.setUint32(24, data.byteLength, true);
      central.view.setUint16(28, name.byteLength, true);
      central.view.setUint16(30, 0, true);
      central.view.setUint16(32, 0, true);
      central.view.setUint16(34, 0, true);
      central.view.setUint16(36, 0, true);
      central.view.setUint32(38, 0, true);
      central.view.setUint32(42, offset, true);
      directory.push(central.bytes, name);
      offset += local.bytes.byteLength + name.byteLength + data.byteLength;
    });

    const directorySize = directory.reduce((total, bytes) => total + bytes.byteLength, 0);
    const end = zipHeader(22);
    end.view.setUint32(0, 0x06054b50, true);
    end.view.setUint16(4, 0, true);
    end.view.setUint16(6, 0, true);
    end.view.setUint16(8, entries.length, true);
    end.view.setUint16(10, entries.length, true);
    end.view.setUint32(12, directorySize, true);
    end.view.setUint32(16, offset, true);
    end.view.setUint16(20, 0, true);
    return new Blob([...parts, ...directory, end.bytes], { type: "application/zip" });
  }

  function parseStoredZip(bytes) {
    const source = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
    const view = new DataView(source.buffer, source.byteOffset, source.byteLength);
    const decoder = new TextDecoder("utf-8");
    const entries = new Map();
    let offset = 0;
    while (offset + 4 <= source.byteLength) {
      const signature = view.getUint32(offset, true);
      if (signature === 0x02014b50 || signature === 0x06054b50) break;
      if (signature !== 0x04034b50 || offset + 30 > source.byteLength) {
        throw new Error("PORTABLE_ZIP_STRUCTURE_INVALID");
      }
      const flags = view.getUint16(offset + 6, true);
      const compression = view.getUint16(offset + 8, true);
      const compressedSize = view.getUint32(offset + 18, true);
      const uncompressedSize = view.getUint32(offset + 22, true);
      const nameLength = view.getUint16(offset + 26, true);
      const extraLength = view.getUint16(offset + 28, true);
      if ((flags & 0x0008) !== 0 || compression !== 0 || compressedSize !== uncompressedSize) {
        throw new Error("PORTABLE_ZIP_COMPRESSION_UNSUPPORTED");
      }
      const nameStart = offset + 30;
      const dataStart = nameStart + nameLength + extraLength;
      const dataEnd = dataStart + compressedSize;
      if (dataEnd > source.byteLength) throw new Error("PORTABLE_ZIP_TRUNCATED");
      const path = decoder.decode(source.slice(nameStart, nameStart + nameLength));
      if (!path || path.startsWith("/") || path.includes("../") || entries.has(path)) {
        throw new Error("PORTABLE_ZIP_PATH_INVALID");
      }
      entries.set(path, source.slice(dataStart, dataEnd));
      if (entries.size > 500) throw new Error("PORTABLE_ZIP_TOO_MANY_ENTRIES");
      offset = dataEnd;
    }
    if (!entries.size) throw new Error("PORTABLE_ZIP_EMPTY");
    return entries;
  }

  function parseJsonEntry(entries, path) {
    const bytes = entries.get(path);
    if (!bytes) throw new Error(`PORTABLE_ENTRY_NOT_FOUND: ${path}`);
    try {
      return JSON.parse(new TextDecoder("utf-8").decode(bytes));
    } catch {
      throw new Error(`PORTABLE_JSON_INVALID: ${path}`);
    }
  }

  function portableManifestPaths(entries) {
    if (entries.has("manifest.json")) return ["manifest.json"];
    if (entries.has("bundle-manifest.json")) {
      const bundle = parseJsonEntry(entries, "bundle-manifest.json");
      if (bundle.package_schema !== "KC_PORTABLE_PHOTO_EXPORT_BUNDLE_V1" || !Array.isArray(bundle.records)) {
        throw new Error("PORTABLE_BUNDLE_MANIFEST_INVALID");
      }
      return bundle.records.map((record) => clean(record.manifest_path)).filter(Boolean);
    }
    const discovered = [...entries.keys()].filter((path) => /(?:^|\/)manifest\.json$/.test(path)).sort();
    if (!discovered.length) throw new Error("PORTABLE_MANIFEST_NOT_FOUND");
    return discovered;
  }

  function portableBasePath(manifestPath) {
    const index = manifestPath.lastIndexOf("/");
    return index < 0 ? "" : manifestPath.slice(0, index + 1);
  }

  function portableExportDataToSnapshot(manifest) {
    const record = manifest.record && typeof manifest.record === "object" ? manifest.record : {};
    const data = record.export_data && typeof record.export_data === "object" ? record.export_data : {};
    const normalizedGauge = gaugeRange(data.gauge_min, data.gauge_max, data.gauge);
    const visitContext = clean(data.visit_context);
    const supplier = clean(data.supplier);
    const sourceEvent = exhibitionForVisitContext(visitContext);
    const supplierMaster = supplierRecordForEvent(sourceEvent, supplier);
    return {
      entryDate: clean(data.entry_date),
      operatorName: "",
      department: "",
      priority: clean(data.priority) || "NORMAL",
      documentType: documentTypeForEditor(data.document_type),
      visitContext,
      sourceEventId: clean(data.source_event_id) || sourceEvent?.id || "",
      supplier,
      supplierMasterId: clean(data.supplier_master_id) || supplierMaster?.supplier_master_id || supplierMaster?.id || "",
      yarnName: clean(data.yarn_name),
      factory: clean(data.factory),
      factoryId: clean(data.factory_id),
      factoryRelationshipId: clean(data.factory_relationship_id),
      factoryReviewStatus: clean(data.factory_review_status),
      factoryNameSnapshot: clean(data.factory_name_snapshot || data.factory),
      abbreviation: clean(data.abbreviation),
      yarnCount: clean(data.yarn_count),
      qualityLabel: clean(data.quality_label),
      specificationText: clean(data.specification_text),
      yarnStructure: clean(data.yarn_structure),
      yarnStructureOther: clean(data.yarn_structure_other),
      composition: clean(data.composition),
      price: clean(data.price),
      currency: clean(data.currency),
      priceUnit: clean(data.price_unit),
      gauge: normalizedGauge.label,
      gaugeMin: normalizedGauge.min,
      gaugeMax: normalizedGauge.max,
      knittingEndCount: normalizeKnittingEndCount(data.knitting_end_count || data.knittingEndCount || data.end_count),
      knitStructure: clean(data.knit_structure),
      knittingTechniques: Array.isArray(data.knitting_techniques) ? data.knitting_techniques.map(clean).filter(Boolean) : [],
      colorSample: clean(data.color_sample),
      bookAvailability: clean(data.book_availability),
      sampleStatus: Array.isArray(data.sample_status) ? data.sample_status.map(clean).filter(Boolean) : [],
      tactileFeelings: (() => {
        const normalized = tactileFeelingsForEditor(data.tactile_feelings);
        return [...normalized.selected, ...normalized.legacy];
      })(),
      attentionRating: attentionRatingForEditor(data.attention_rating, data.priority),
      developmentActions: Array.isArray(data.development_actions) ? data.development_actions.map(clean).filter(Boolean) : [],
      functionalFiberUsage: clean(data.functional_fiber_usage),
      functionalFiberDetail: clean(data.functional_fiber_detail),
      sustainableFiberUsage: clean(data.sustainable_fiber_usage),
      sustainableFiberDetail: clean(data.sustainable_fiber_detail),
      actualCountStructure: clean(data.actual_count_structure),
      spinningMethod: canonicalSpinningMethod(data.spinning_method),
      spinningMethodOther: clean(data.spinning_method_other),
      filamentTypeObservation: canonicalFilamentType(data.filament_type_observation),
      filamentTypeOther: clean(data.filament_type_other),
      compositeStructureObservation: clean(data.composite_structure_observation),
      compositeStructureOther: clean(data.composite_structure_other),
      processingMethod: clean(data.processing_method),
      coveringStructure: clean(data.covering_structure),
      outerFilament: Array.isArray(data.outer_filament) ? data.outer_filament.map(clean).filter(Boolean) : [],
      seasons: seasonsForEditor(data.seasons),
      bookRequest: clean(data.book_request),
      fabricRequest: clean(data.fabric_request),
      arrangementMemo: clean(data.arrangement_memo),
      researchRequest: clean(data.research_request),
      notes: clean(data.notes),
      sourceDataState: clean(record.data_state) || "DRAFT",
      portableImport: {
        package_schema: clean(manifest.package_schema),
        package_version: clean(manifest.package_version),
        export_id: clean(manifest.export_id),
        exported_at: clean(manifest.exported_at)
      }
    };
  }

  function safeFileSegment(value, fallback = "record") {
    const normalized = String(value || fallback).normalize("NFKC")
      .replace(/[^A-Za-z0-9._-]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 80);
    return normalized || fallback;
  }

  function photoExtension(record) {
    if (record.mediaType === "image/png") return "png";
    if (record.mediaType === "image/webp") return "webp";
    return "jpg";
  }

  function buildPortableExportData(snapshot) {
    const normalizedGauge = gaugeRange(snapshot.gaugeMin, snapshot.gaugeMax, snapshot.gauge);
    return {
      entry_date: snapshot.entryDate || "",
      priority: snapshot.priority || "",
      document_type: snapshot.documentType || "",
      visit_context: snapshot.visitContext || "",
      source_event_id: snapshot.sourceEventId || "",
      supplier: snapshot.supplier || "",
      supplier_master_id: snapshot.supplierMasterId || "",
      yarn_name: snapshot.yarnName || "",
      factory: snapshot.factory || "",
      factory_id: snapshot.factoryId || "",
      factory_relationship_id: snapshot.factoryRelationshipId || "",
      factory_review_status: snapshot.factoryReviewStatus || "",
      factory_name_snapshot: snapshot.factoryNameSnapshot || snapshot.factory || "",
      abbreviation: snapshot.abbreviation || "",
      yarn_count: snapshot.yarnCount || "",
      quality_label: snapshot.qualityLabel || "",
      specification_text: snapshot.specificationText || "",
      yarn_structure: snapshot.yarnStructure || "",
      yarn_structure_other: snapshot.yarnStructureOther || "",
      composition: snapshot.composition || "",
      price: snapshot.price || "",
      currency: snapshot.currency || "",
      price_unit: snapshot.priceUnit || "",
      gauge: normalizedGauge.label,
      gauge_min: normalizedGauge.min,
      gauge_max: normalizedGauge.max,
      knitting_end_count: normalizeKnittingEndCount(snapshot.knittingEndCount),
      knit_structure: snapshot.knitStructure || "",
      knitting_techniques: Array.isArray(snapshot.knittingTechniques) ? [...snapshot.knittingTechniques] : [],
      color_sample: snapshot.colorSample || "",
      book_availability: snapshot.bookAvailability || "",
      sample_status: Array.isArray(snapshot.sampleStatus) ? [...snapshot.sampleStatus] : [],
      tactile_feelings: Array.isArray(snapshot.tactileFeelings) ? [...snapshot.tactileFeelings] : [],
      attention_rating: snapshot.attentionRating || "",
      development_actions: Array.isArray(snapshot.developmentActions) ? [...snapshot.developmentActions] : [],
      functional_fiber_usage: snapshot.functionalFiberUsage || "",
      functional_fiber_detail: snapshot.functionalFiberDetail || "",
      sustainable_fiber_usage: snapshot.sustainableFiberUsage || "",
      sustainable_fiber_detail: snapshot.sustainableFiberDetail || "",
      actual_count_structure: snapshot.actualCountStructure || "",
      spinning_method: snapshot.spinningMethod || "",
      spinning_method_other: snapshot.spinningMethodOther || "",
      filament_type_observation: snapshot.filamentTypeObservation || "",
      filament_type_other: snapshot.filamentTypeOther || "",
      composite_structure_observation: snapshot.compositeStructureObservation || "",
      composite_structure_other: snapshot.compositeStructureOther || "",
      processing_method: snapshot.processingMethod || "",
      covering_structure: snapshot.coveringStructure || "",
      outer_filament: Array.isArray(snapshot.outerFilament) ? [...snapshot.outerFilament] : [],
      seasons: Array.isArray(snapshot.seasons) ? [...snapshot.seasons] : [],
      book_request: snapshot.bookRequest || "",
      fabric_request: snapshot.fabricRequest || "",
      arrangement_memo: snapshot.arrangementMemo || "",
      research_request: snapshot.researchRequest || "",
      notes: snapshot.notes || ""
    };
  }

  function buildPortableExportManifest(event, photoItems, exportedAt, exportId, exportData, exportDataSha256, companyRow, companyCsvSha256) {
    return {
      package_schema: CONTRACT.portable_export_schema,
      package_version: "1.1",
      export_id: exportId,
      exported_at: exportedAt,
      source: {
        source_system: "KNIT_COMPASS_PHOTO_CAPTURE",
        app_version: CONTRACT.version,
        history_policy: CONTRACT.history_policy,
        automatic_sync: CONTRACT.automatic_sync
      },
      portability: {
        purpose: "KNIT_COMPASS_ASSET_AND_EMPLOYER_EXTERNAL_IMPORT",
        destination: "ANY_AUTHORIZED_COMPUTER",
        employer_neutral_core: true,
        google_account_connection: "NONE",
        automatic_upload: "OFF",
        write_back: "OFF",
        selected_record_only: true,
        photo_limit: MAX_PHOTOS_PER_RECORD,
        photo_category_order: PHOTO_TYPES.map((type) => type.key),
        source_field_policy: "COMPANY_FIELDS_ARE_A_SUBSET_OF_PERSONAL_FIELDS"
      },
      adapters: [{
        adapter_schema: CONTRACT.company_adapter_schema,
        file: COMPANY_IMPORT_FILE,
        sha256: companyCsvSha256,
        target_sheet: "EXISTING_COMPANY_CONFIGURED_SHEET",
        import_actor: "COMPANY_ACCOUNT_ONLY",
        automatic_connection: "OFF",
        company_identity_fields: "COMPANY_SCRIPT_PROPERTIES_ONLY"
      }],
      record: {
        record_id: event.recordId,
        event_id: event.eventId,
        version: event.version,
        event_type: event.eventType,
        data_state: event.dataState,
        human_review_status: event.humanReviewStatus,
        created_at: event.createdAt,
        updated_at: event.updatedAt,
        export_data_sha256: exportDataSha256,
        export_data: exportData,
        company_import: companyRow,
        company_spreadsheet_payload_schema: CONTRACT.company_spreadsheet_payload_schema,
        company_spreadsheet_payload: buildCompanySpreadsheetPayload(exportData, photoItems.length, event.recordId)
      },
      photos: photoItems.map((item) => ({
        photo_id: item.record.photoId,
        type: ["product", "yarn", "yarn_book"].includes(item.record.type) ? item.record.type : "yarn",
        capture_type: item.record.type,
        label: item.record.label,
        file_name: item.record.fileName,
        original_file_name: item.record.originalFileName || "",
        zip_path: item.path,
        media_type: item.record.mediaType,
        size_bytes: item.bytes.byteLength,
        sha256: item.sha256,
        captured_at: item.record.capturedAt,
        orientation: {
          capture_source: item.record.captureSource,
          original: item.record.captureOrientationOriginal,
          final: item.record.captureOrientationFinal,
          normalized: item.record.orientationNormalized,
          manual_rotation_degree: item.record.manualRotationDegree,
          original_exif_orientation: item.record.originalExifOrientation,
          pixel_width: item.record.pixelWidth,
          pixel_height: item.record.pixelHeight
        }
      }))
    };
  }

  function csvCell(value) {
    const raw = Array.isArray(value) ? value.join(" / ") : String(value ?? "");
    const safe = /^[=+\-@\t\r]/.test(raw) ? `'${raw}` : raw;
    return `"${safe.replaceAll('"', '""')}"`;
  }

  function buildCsv(headers, row) {
    return `\ufeff${headers.map(csvCell).join(",")}\r\n${headers.map((header) => csvCell(row[header] ?? "")).join(",")}\r\n`;
  }

  function buildPortableCsv(exportData, photoItems) {
    const photoPaths = groupPhotoPaths(photoItems);
    const joined = (type) => (photoPaths[type] || []).join(" / ");
    const headers = [
      "更新日時", "登録日", "重要度", "資料分類", "入手経路", "展示会ID", "Supplier", "糸商マスターID", "糸名・素材名", "シーズン", "設定工場",
      "工場ID", "工場取引関係ID", "工場確認状態", "撮影時工場名",
      "略称", "番手", "混率", "品質表示", "規格", "糸構造", "糸構造補足", "価格", "通貨", "価格単位",
      "対応ゲージ（目安）", "最小ゲージ", "最大ゲージ", "本取り", "編地組織",
      "編成技術", "カラー見本（旧互換）", "BOOK掲載状況", "手元にある見本", "触感・風合い", "重要度（5段階）", "開発アクション",
      "機能性繊維使用", "機能性繊維詳細", "サステナブル繊維使用", "サステナブル繊維詳細",
      "実番手・構造", "精紡方式（仮入力）", "精紡方式その他補足", "フィラメント種類",
      "フィラメント種類その他補足", "複合構造", "複合構造その他補足", "加工方法", "カバリング構造", "外層フィラメント",
      "BOOK手配", "編地手配", "手配メモ", "糸の調査依頼", "メモ",
      "表紙・全体写真ファイル", "糸・素材本体写真ファイル", "編地・質感写真ファイル",
      "色見本写真ファイル", "品質表示・規格写真ファイル", "WeChat・連絡記録写真ファイル", "その他写真ファイル",
      "商品写真ファイル（旧分類）", "糸写真ファイル（旧分類）", "糸帳写真ファイル（旧分類）"
    ];
    const values = [
      exportData.updated_at, exportData.entry_date, exportData.priority, exportData.document_type, exportData.visit_context, exportData.source_event_id,
      exportData.supplier, exportData.supplier_master_id, exportData.yarn_name, exportData.seasons, exportData.factory,
      exportData.factory_id, exportData.factory_relationship_id, exportData.factory_review_status, exportData.factory_name_snapshot,
      exportData.abbreviation, exportData.yarn_count, exportData.composition, exportData.quality_label,
      exportData.specification_text,
      exportData.yarn_structure, exportData.yarn_structure_other,
      exportData.price, exportData.currency, exportData.price_unit,
      exportData.gauge, exportData.gauge_min, exportData.gauge_max, exportData.knitting_end_count,
      exportData.knit_structure, exportData.knitting_techniques, exportData.color_sample, exportData.book_availability,
      exportData.sample_status, exportData.tactile_feelings, exportData.attention_rating, exportData.development_actions,
      exportData.functional_fiber_usage, exportData.functional_fiber_detail,
      exportData.sustainable_fiber_usage, exportData.sustainable_fiber_detail,
      exportData.actual_count_structure, exportData.spinning_method,
      exportData.spinning_method_other, exportData.filament_type_observation, exportData.filament_type_other,
      exportData.composite_structure_observation, exportData.composite_structure_other, exportData.processing_method, exportData.covering_structure,
      exportData.outer_filament, exportData.book_request, exportData.fabric_request, exportData.arrangement_memo,
      exportData.research_request, exportData.notes,
      joined("cover"), joined("material"), joined("fabric"), joined("color"), joined("specification"), joined("wechat"), joined("other"),
      joined("product"), joined("yarn"), joined("yarn_book")
    ];
    return `\ufeff${headers.map(csvCell).join(",")}\r\n${values.map(csvCell).join(",")}\r\n`;
  }

  function deriveCompanyYarnStructure(exportData) {
    if (clean(exportData.yarn_structure) === "その他" && clean(exportData.yarn_structure_other)) return clean(exportData.yarn_structure_other);
    if (clean(exportData.yarn_structure) && !["未確認", "不明"].includes(clean(exportData.yarn_structure))) return clean(exportData.yarn_structure);
    if (clean(exportData.composite_structure_observation) && exportData.composite_structure_observation !== "不明") {
      return exportData.composite_structure_observation === "その他"
        ? clean(exportData.composite_structure_other)
        : exportData.composite_structure_observation;
    }
    if (["SCY", "DCY"].includes(exportData.covering_structure)) return exportData.covering_structure;
    const canonicalFilament = canonicalFilamentType(exportData.filament_type_observation);
    if (canonicalFilament && canonicalFilament !== "その他") {
      return canonicalFilament;
    }
    if (exportData.filament_type_observation === "その他" && clean(exportData.filament_type_other)) return clean(exportData.filament_type_other);
    if (exportData.outer_filament?.includes("PET_FDY")) return "FDY";
    if (exportData.outer_filament?.some((value) => /DTY/.test(value))) return "DTY";
    if (clean(exportData.spinning_method) && !["Unknown", "不明", "未確認"].includes(exportData.spinning_method)) {
      return exportData.spinning_method === "その他" ? clean(exportData.spinning_method_other) : exportData.spinning_method;
    }
    return "";
  }

  function companyImportance(priority) {
    if (priority === "URGENT") return "★★★（すぐ見てほしい）";
    if (priority === "HIGH") return "★★（気になる）";
    return "★（参考）";
  }

  function companyDocumentType(documentType) {
    const value = clean(documentType);
    const mapped = {
      "糸カード": "糸",
      "糸・素材": "糸",
      "編地・スワッチ": "編地",
      "編地カード": "編地",
      "スワッチ": "編地"
    };
    return mapped[value] || value;
  }

  function buildCompanyImportRow(exportData, photoItems, exportId) {
    void exportId;
    const orderedPhotos = sortPhotoEntries(photoItems).slice(0, MAX_PHOTOS_PER_RECORD).map((item) => item.path).filter(Boolean);
    const row = Object.fromEntries(COMPANY_IMPORT_HEADERS.map((header) => [header, ""]));
    Object.assign(row, {
      capture_date: formatJstDate(exportData.updated_at),
      operator_name: "",
      department: "",
      document_type: companyDocumentType(exportData.document_type),
      visit_context: exportData.visit_context,
      supplier: exportData.supplier,
      yarn_name: exportData.yarn_name,
      season: (exportData.seasons || []).join(" / "),
      factory: exportData.factory,
      importance: exportData.attention_rating || companyImportance(exportData.priority),
      yarn_count_spec: [exportData.yarn_count, exportData.specification_text].map(clean).filter(Boolean).join(" / "),
      yarn_structure: deriveCompanyYarnStructure(exportData),
      composition: exportData.composition,
      price: exportData.price,
      currency: exportData.currency,
      gauge: exportData.gauge,
      knit_structure: exportData.knit_structure,
      tactile_feeling: (exportData.tactile_feelings || []).join(" / "),
      functional_fiber_usage: exportData.functional_fiber_usage,
      memo: [
        exportData.notes,
        exportData.knitting_end_count ? `本取り: ${exportData.knitting_end_count}本` : "",
        exportData.functional_fiber_detail ? `機能性繊維詳細: ${exportData.functional_fiber_detail}` : "",
        exportData.sustainable_fiber_usage ? `サステナブル繊維使用: ${exportData.sustainable_fiber_usage}` : "",
        exportData.sustainable_fiber_detail ? `サステナブル繊維詳細: ${exportData.sustainable_fiber_detail}` : ""
      ].map(clean).filter(Boolean).join(" / "),
      book_request: exportData.book_request,
      fabric_request: exportData.fabric_request,
      arrangement_memo: exportData.arrangement_memo,
      research_request: exportData.research_request
    });
    orderedPhotos.forEach((path, index) => { row[`photo_${index + 1}`] = path; });
    return row;
  }

  function buildCompanySpreadsheetPayload(exportData, photoCount, sourceCaptureId = "") {
    return {
      sourceCaptureId: clean(sourceCaptureId),
      operatorName: "",
      department: "",
      entryDate: clean(exportData.entry_date) || (clean(exportData.updated_at) ? formatJstDate(exportData.updated_at) : ""),
      category: companyDocumentType(exportData.document_type),
      season: (exportData.seasons || []).join(" / "),
      eventName: clean(exportData.visit_context),
      eventId: clean(exportData.source_event_id),
      supplier: clean(exportData.supplier),
      supplierMasterId: clean(exportData.supplier_master_id),
      materialName: clean(exportData.yarn_name),
      countSpec: [exportData.yarn_count, exportData.specification_text].map(clean).filter(Boolean).join(" / "),
      yarnStructure: deriveCompanyYarnStructure(exportData),
      composition: clean(exportData.composition),
      functionalFiber: clean(exportData.functional_fiber_usage) || "未確認",
      functionalFiberDetail: clean(exportData.functional_fiber_detail),
      sustainableFiber: clean(exportData.sustainable_fiber_usage) || "未確認",
      sustainableFiberDetail: clean(exportData.sustainable_fiber_detail),
      price: clean(exportData.price),
      currency: clean(exportData.currency),
      gauge: clean(exportData.gauge),
      knittingEndCount: normalizeKnittingEndCount(exportData.knitting_end_count),
      knitStructure: clean(exportData.knit_structure),
      feels: Array.isArray(exportData.tactile_feelings) ? [...exportData.tactile_feelings] : [],
      importance: clean(exportData.attention_rating) || companyImportance(exportData.priority),
      memo: clean(exportData.notes),
      factoryName: clean(exportData.factory),
      bookArrangement: clean(exportData.book_request),
      fabricArrangement: clean(exportData.fabric_request),
      arrangementMemo: clean(exportData.arrangement_memo),
      yarnResearchRequest: clean(exportData.research_request),
      photoCount: Math.max(0, Math.min(MAX_PHOTOS_PER_RECORD, Number(photoCount) || 0))
    };
  }

  function buildCompanyImportCsv(companyRow) {
    return buildCsv(COMPANY_IMPORT_HEADERS, companyRow);
  }

  async function exportPortablePackage(recordId) {
    if (state.exportingRecords.has(recordId)) return;
    const event = state.latestRecords.find((item) => item.recordId === recordId);
    if (!event) throw new Error("EXPORT_RECORD_NOT_FOUND");
    state.exportingRecords.add(recordId);
    renderRecords();
    setMessage("kcInboxMessage", "外部取込ZIPを作成しています。写真が多い場合は少しお待ちください。");
    try {
      const photoItems = [];
      for (const ref of sortPhotoEntries(event.snapshot.photoRefs || [])) {
        const record = await getOne(STORES.photos, ref.photoId);
        if (!record?.blob) throw new Error(`PHOTO_NOT_FOUND: ${ref.photoId}`);
        const bytes = new Uint8Array(await record.blob.arrayBuffer());
        const path = `photos/${safeFileSegment(record.type, "photo")}_${safeFileSegment(record.photoId)}.${photoExtension(record)}`;
        photoItems.push({ record, bytes, path, sha256: await sha256Hex(bytes) });
      }
      const exportedAt = isoNow();
      const exportId = createId("KCI-EXPORT");
      const exportData = { ...buildPortableExportData(event.snapshot), updated_at: event.updatedAt };
      const exportDataSha256 = await snapshotHash(exportData);
      const csvBytes = new TextEncoder().encode(buildPortableCsv(exportData, photoItems));
      const companyRow = buildCompanyImportRow(exportData, photoItems, exportId);
      const companyCsvBytes = new TextEncoder().encode(buildCompanyImportCsv(companyRow));
      const companyCsvSha256 = await sha256Hex(companyCsvBytes);
      const manifest = buildPortableExportManifest(event, photoItems, exportedAt, exportId, exportData, exportDataSha256, companyRow, companyCsvSha256);
      const manifestBytes = new TextEncoder().encode(`${JSON.stringify(manifest, null, 2)}\n`);
      const readmeBytes = new TextEncoder().encode([
        "Knit Compass Dual-use Photo Export",
        "",
        "KnitCompass_Data.csv: 勤務先に依存しない共通データです。",
        `${COMPANY_IMPORT_FILE}: 会社側の外部取込で使用するCSVです。`,
        "photos/: 表紙・全体、糸・素材本体、編地・質感、色見本、品質表示・規格、WeChat・連絡記録、その他の写真です。CSV内の相対パスと対応します。",
        "写真は合計10枚まで。同じ分類に複数枚を保存できます。旧版の商品・糸・糸帳写真も失わず保持します。",
        "",
        "Knit Compass Photo Capture 2.1.43 独立版は、写真と素材情報をこの端末のDRAFTとして扱います。",
        "機能性繊維詳細・サステナブル繊維使用/詳細はmanifest.jsonのcompany_spreadsheet_payloadにも保持します。旧CSV取込ではメモ欄へ補足します。",
        "略称・実番手・詳細紡績方式・加工方法・カバリング詳細など、会社側取込対象外の情報はKnitCompass_Data.csvだけに残ります。",
        "担当者名と部署は空欄です。会社側の取込処理が、会社管理の設定値だけを補います。",
        "個人端末は組織アカウントや共有ストレージへ自動接続しません。",
        "ZIPは管理端末へ移し、権限内の外部取込処理で登録してください。",
        "転職後もKnitCompass_Data.csvを共通原本として利用し、新しい会社側だけで変換します。",
        "個人アカウントID、表示名、メール、パスフレーズ、認証情報は含まれていません。"
      ].join("\r\n"));
      const checksumLines = [
        `${await sha256Hex(manifestBytes)}  manifest.json`,
        `${await sha256Hex(csvBytes)}  KnitCompass_Data.csv`,
        `${companyCsvSha256}  ${COMPANY_IMPORT_FILE}`,
        `${await sha256Hex(readmeBytes)}  README.txt`
      ]
        .concat(photoItems.map((item) => `${item.sha256}  ${item.path}`));
      const checksumBytes = new TextEncoder().encode(`${checksumLines.join("\n")}\n`);
      const zip = buildStoredZip([
        { path: "manifest.json", bytes: manifestBytes },
        { path: "KnitCompass_Data.csv", bytes: csvBytes },
        { path: COMPANY_IMPORT_FILE, bytes: companyCsvBytes },
        { path: "README.txt", bytes: readmeBytes },
        { path: "SHA256SUMS.txt", bytes: checksumBytes },
        ...photoItems.map((item) => ({ path: item.path, bytes: item.bytes }))
      ], new Date(exportedAt));
      const timestamp = exportedAt.replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
      const subject = safeFileSegment(event.snapshot.yarnName || event.recordId, "record");
      const file = new File([zip], `KnitCompass_ExternalImport_${subject}_${timestamp}.zip`, { type: "application/zip", lastModified: Date.now() });
      triggerFileDownload(file);
      setMessage("kcInboxMessage", "外部取込ZIPを書き出しました。管理端末へ移し、Knit Compass Photo Captureへ外部取込してください。個人アカウントからの自動接続はありません。");
    } finally {
      state.exportingRecords.delete(recordId);
      renderRecords();
    }
  }

  async function uploadPortableManifest(entries, manifestPath) {
    const manifest = parseJsonEntry(entries, manifestPath);
    if (manifest.package_schema !== "KC_PORTABLE_PHOTO_EXPORT_V1") {
      throw new Error(`PORTABLE_SCHEMA_UNSUPPORTED: ${clean(manifest.package_schema) || "UNKNOWN"}`);
    }
    const record = manifest.record && typeof manifest.record === "object" ? manifest.record : {};
    const sourceAppVersion = clean(manifest.source?.app_version);
    const sourceVersionMatch = sourceAppVersion.match(/^2\.1\.(41|42|43)(?:\b|[- ])/);
    const importSource = sourceVersionMatch
      ? `PHOTO_CAPTURE_2_1_${sourceVersionMatch[1]}_PORTABLE_ZIP`
      : "PHOTO_CAPTURE_PORTABLE_ZIP";
    const recordId = clean(record.record_id);
    if (!/^KCI-CAPTURE-[0-9a-f-]{36}$/i.test(recordId) || !record.export_data || typeof record.export_data !== "object") {
      throw new Error("PORTABLE_RECORD_INVALID");
    }
    const exportDataHash = await snapshotHash(record.export_data);
    if (clean(record.export_data_sha256) && exportDataHash !== clean(record.export_data_sha256)) {
      throw new Error(`PORTABLE_RECORD_HASH_MISMATCH: ${recordId}`);
    }
    const basePath = portableBasePath(manifestPath);
    const photos = Array.isArray(manifest.photos) ? manifest.photos : [];
    if (photos.length > MAX_PHOTOS_PER_RECORD) throw new Error(`PORTABLE_PHOTO_COUNT_INVALID: ${recordId}`);
    const photoRows = [];
    for (const photo of photos) {
      const relativePath = clean(photo.zip_path);
      const bytes = entries.get(`${basePath}${relativePath}`);
      if (!relativePath || !bytes) throw new Error(`PORTABLE_PHOTO_NOT_FOUND: ${relativePath || recordId}`);
      const actualHash = await sha256Hex(bytes);
      if (clean(photo.sha256) && actualHash !== clean(photo.sha256)) {
        throw new Error(`PORTABLE_PHOTO_HASH_MISMATCH: ${relativePath}`);
      }
      const fileName = clean(photo.file_name) || relativePath.split("/").pop() || `${clean(photo.photo_id) || "photo"}.jpg`;
      const mediaType = clean(photo.media_type) || (/\.png$/i.test(fileName) ? "image/png" : /\.webp$/i.test(fileName) ? "image/webp" : "image/jpeg");
      photoRows.push({
        manifest: {
          photo_id: clean(photo.photo_id),
          type: clean(photo.type) || "other",
          label: clean(photo.label),
          file_name: fileName
        },
        file: new File([bytes], fileName, { type: mediaType })
      });
    }
    const ownerManifest = {
      schema_version: "KC_OWNER_INBOX_UPLOAD_V1",
      record_id: recordId,
      event_id: clean(record.event_id),
      version: Number(record.version) || 1,
      event_type: clean(record.event_type) || "CREATE",
      data_state: clean(record.data_state) || "DRAFT",
      updated_at: clean(record.updated_at || record.export_data.updated_at || manifest.exported_at),
      snapshot: portableExportDataToSnapshot(manifest),
      photos: photoRows.map((row) => row.manifest)
    };
    const existingEvents = await getAll(STORES.events);
    const duplicate = existingEvents.some((event) =>
      event.eventId === ownerManifest.event_id
      || (event.recordId === ownerManifest.record_id && Number(event.version) === Number(ownerManifest.version))
    );
    if (duplicate) return { duplicate: true };

    const now = isoNow();
    const photoRefs = photoRows.map(({ manifest: photo }) => ({
      photoId: photo.photo_id || createId("KCI-PHOTO"),
      type: photo.type || "other",
      label: photo.label || photoTypeDefinition(photo.type).label,
      fileName: photo.file_name,
      capturedAt: ownerManifest.updated_at || now
    }));
    const snapshot = { ...ownerManifest.snapshot, photoRefs };
    const eventRecord = {
      eventId: ownerManifest.event_id || createId("KCI-EVENT"),
      recordId: ownerManifest.record_id,
      version: ownerManifest.version,
      eventType: ownerManifest.event_type,
      dataState: "DRAFT",
      humanReviewStatus: "NOT_REVIEWED",
      originalPhotoIds: photoRefs.map((photo) => photo.photoId),
      actorId: state.session.accountId,
      actorDisplayName: state.session.displayName,
      createdAt: ownerManifest.updated_at || now,
      updatedAt: ownerManifest.updated_at || now,
      snapshot,
      historyPolicy: "APPEND_ONLY",
      automaticSync: "OFF",
      automaticPublish: "OFF",
      importedFrom: importSource
    };
    const auditRecord = {
      auditId: createId("KCI-AUDIT"),
      eventId: eventRecord.eventId,
      recordId: eventRecord.recordId,
      version: eventRecord.version,
      eventType: eventRecord.eventType,
      dataState: "DRAFT",
      humanReviewStatus: "NOT_REVIEWED",
      originalPhotoIds: eventRecord.originalPhotoIds,
      actorId: state.session.accountId,
      registeredAt: eventRecord.createdAt,
      updatedAt: eventRecord.updatedAt,
      createdAt: now,
      snapshotSha256: await snapshotHash(snapshot),
      auditRealm: CONTRACT.audit_store,
      importedFrom: eventRecord.importedFrom
    };
    const transaction = state.db.transaction([STORES.events, STORES.audit, STORES.photos], "readwrite");
    transaction.objectStore(STORES.events).add(eventRecord);
    transaction.objectStore(STORES.audit).add(auditRecord);
    photoRows.forEach(({ file }, index) => {
      const ref = photoRefs[index];
      transaction.objectStore(STORES.photos).add({
        photoId: ref.photoId,
        recordId: eventRecord.recordId,
        type: ref.type,
        label: ref.label,
        fileName: ref.fileName,
        blob: file,
        capturedAt: ref.capturedAt,
        importedFrom: eventRecord.importedFrom
      });
    });
    await transactionPromise(transaction);
    window.KnitCompassBackup?.notifyDataChanged?.(eventRecord.updatedAt);
    return { duplicate: false, imported: true };
  }

  async function importPortableFiles(fileList) {
    if (state.isPortableImporting) return;
    const files = [...fileList].filter((file) => file instanceof File && file.size > 0);
    if (!files.length) return;
    state.isPortableImporting = true;
    const input = document.getElementById("kcPortableImport");
    input.disabled = true;
    let uploaded = 0;
    let duplicates = 0;
    let recordTotal = 0;
    const failures = [];
    try {
      for (const file of files) {
        if (file.size > MAX_PORTABLE_ZIP_BYTES) {
          failures.push(`${file.name}: ZIP容量が上限を超えています`);
          continue;
        }
        try {
          const entries = parseStoredZip(new Uint8Array(await file.arrayBuffer()));
          const manifestPaths = portableManifestPaths(entries);
          recordTotal += manifestPaths.length;
          for (let index = 0; index < manifestPaths.length; index += 1) {
            setMessage("kcInboxMessage", `${file.name}: ${index + 1} / ${manifestPaths.length}件を検証して端末へ移植しています。画面を閉じずにお待ちください。`);
            try {
              const result = await uploadPortableManifest(entries, manifestPaths[index]);
              if (result?.duplicate) duplicates += 1;
              else uploaded += 1;
            } catch (error) {
              failures.push(`${manifestPaths[index]}: ${error.message || error}`);
            }
          }
        } catch (error) {
          failures.push(`${file.name}: ${error.message || error}`);
        }
      }
      await loadEvents();
      refreshCandidateOptions();
      renderRecords();
      const summary = `2.1.41〜2.1.43移植：対象${recordTotal}件、新規${uploaded}件、移植済み${duplicates}件`;
      setMessage(
        "kcInboxMessage",
        failures.length ? `${summary}、失敗${failures.length}件（${failures.join(" / ")}）` : `${summary}。原本は変更せず、独立版の端末内DRAFTへ追加しました。`,
        failures.length > 0
      );
    } finally {
      state.isPortableImporting = false;
      input.disabled = false;
      input.value = "";
    }
  }

  function sessionErrorTemplate(message) {
    return `
      <main class="kc-app kc-auth-wrap">
        <section class="kc-auth-card" aria-labelledby="kcAuthTitle">
          <p class="kc-eyebrow">独立Photo Capture</p>
          <h1 id="kcAuthTitle">Knit Compass Photo Capture</h1>
          <p class="kc-lead">端末内DRAFTを開けませんでした。別のPhoto Capture画面を閉じてから、もう一度お試しください。</p>
          <a class="kc-file-button" href="${escapeHtml(`${window.location.pathname}?build=2.1.43-independent.1`)}">再読み込み</a>
          <a class="kc-file-button secondary" href="https://knit-compass-v04.s-zhujing.chatgpt.site/">Knit Compass V04へ戻る</a>
          <p class="kc-message error" role="status">${escapeHtml(message)}</p>
        </section>
      </main>`;
  }

  function photoSlotTemplate(type, options = {}) {
    const title = options.title || type.label;
    const description = options.description || type.description;
    const badge = options.badge || "PRIVATE";
    const isSpecification = type.key === "specification";
    const isCommunication = type.key === "wechat";
    return `
      <article class="kc-photo-slot${isSpecification ? " specification" : ""}${isCommunication ? " communication" : ""}" data-photo-slot="${type.key}">
        <div class="kc-photo-heading"><div><h4>${escapeHtml(title)}</h4><p>${escapeHtml(description)}</p></div><span class="kc-badge">${escapeHtml(badge)}</span></div>
        <div class="kc-photo-input-actions" aria-label="${escapeHtml(title)}の入力方法">
          <label class="kc-file-button">カメラで撮影
            <input class="kc-visually-hidden-file" type="file" accept="image/*" capture="environment" data-photo-input="${type.key}" data-photo-source="camera">
          </label>
          <label class="kc-file-button secondary">写真から選択
            <input class="kc-visually-hidden-file" type="file" accept="image/*" multiple data-photo-input="${type.key}" data-photo-source="library">
          </label>
        </div>
        <p class="kc-field-hint kc-photo-guide">この分類に複数枚追加できます。撮影後に向きを自動補正します。</p>
        <div class="kc-photo-preview" data-photo-preview="${type.key}">
          <div class="kc-photo-placeholder">写真はまだ選択されていません</div>
        </div>
      </article>`;
  }

  function checkboxOptionsTemplate(name, values) {
    return values.map((value) => `
      <label><input type="checkbox" name="${escapeHtml(name)}" value="${escapeHtml(value)}">${escapeHtml(value)}</label>`).join("");
  }

  function selectOptionsTemplate(values) {
    return values.map((value) => `<option>${escapeHtml(value)}</option>`).join("");
  }

  function bookAvailabilityOptionsTemplate() {
    return BOOK_AVAILABILITY_VALUES.map((value) =>
      `<option value="${escapeHtml(value)}">${escapeHtml(BOOK_AVAILABILITY_LABELS[value] || value)}</option>`
    ).join("");
  }

  function bookAvailabilityLabel(value) {
    return BOOK_AVAILABILITY_LABELS[clean(value)] || clean(value);
  }

  function sampleStatusForEditor(values, legacyColorSample = "") {
    const selected = Array.isArray(values) ? values.map(clean).filter(Boolean) : [];
    if (clean(legacyColorSample) === "あり" && !selected.includes(BOOK_SAMPLE_STATUS)) selected.push(BOOK_SAMPLE_STATUS);
    return [...new Set(selected)];
  }

  function spinningMethodOptionsTemplate() {
    return SPINNING_METHODS.map((value) =>
      `<option value="${escapeHtml(value)}">${escapeHtml(SPINNING_METHOD_LABELS[value] || value)}</option>`
    ).join("");
  }

  function filamentTypeOptionsTemplate() {
    return FILAMENT_TYPES.map((value) =>
      `<option value="${escapeHtml(value)}">${escapeHtml(FILAMENT_TYPE_LABELS[value] || value)}</option>`
    ).join("");
  }

  function tactileFeelingTemplate() {
    return checkboxOptionsTemplate("tactile_feelings", TACTILE_FEELINGS);
  }

  function appTemplate() {
    return `
      <main class="kc-app kc-shell">
        <header class="kc-topbar">
          <div class="kc-brand">
            <p class="kc-eyebrow">PHOTO CAPTURE</p>
            <h1>写真から素材情報を登録する</h1>
            <p class="kc-lead">展示会や訪問先で、写真と素材情報を端末内DRAFTとして記録します。必要な記録だけを外部取込ZIPとして書き出し、正式マスターへは内容を確認してから反映します。</p>
            <div class="kc-build-info" aria-label="画面バージョン情報">
              <span>画面バージョン <strong>${escapeHtml(BUILD_INFO.version)}</strong></span>
              <span>最終更新 <time datetime="${escapeHtml(BUILD_INFO.updated_at)}">${escapeHtml(BUILD_INFO.updated_label)}</time></span>
            </div>
          </div>
          <div>
            <div class="kc-badges" aria-label="保存と確認の流れ">
              <span class="kc-badge safe">端末に下書き保存</span>
              <span class="kc-badge safe">受信箱で内容確認</span>
              <span class="kc-badge">正式登録は人が確認</span>
            </div>
            <div class="kc-session">
              <span id="kcSessionIdentity"></span>
              <button type="button" class="ghost" id="kcLogout">利用者を切り替える</button>
            </div>
          </div>
        </header>

        <section class="kc-panel" id="kcInbox" aria-labelledby="kcInboxTitle">
          <div class="kc-panel-heading">
            <div>
              <p class="kc-eyebrow">Capture Inbox</p>
              <h2 id="kcInboxTitle">写真登録</h2>
              <p class="kc-muted">保存済みの最新値を表示します。CREATE／UPDATEの全イベントは別に保持されます。</p>
            </div>
            <div class="kc-primary-actions">
              <button type="button" id="kcNewCapture">写真を撮る・素材を登録</button>
            </div>
          </div>
          <div id="kcConnectivityStatus" class="kc-connectivity-status" role="status" aria-live="polite" data-connectivity="${state.isOnline ? "online" : "offline"}">
            <strong id="kcConnectivityLabel">${state.isOnline ? "通信あり" : "通信なし"}</strong>
            <span id="kcConnectivityDetail">端末保存と外部取込ZIPの書き出しを利用できます。</span>
          </div>
          <div class="kc-search" role="search">
            <label>全体検索
              <input id="kcSearchAll" type="search" placeholder="Capture ID、Supplier、糸名、略称、番手">
            </label>
            <label>Supplier検索
              <input id="kcSearchSupplier" type="search" list="kcSupplierSearchOptions" autocomplete="off" placeholder="選択または入力">
            </label>
            <label>糸名検索
              <input id="kcSearchYarnName" type="search" list="kcYarnNameSearchOptions" autocomplete="off" placeholder="選択または入力">
            </label>
            <label>略称検索
              <input id="kcSearchAbbreviation" type="search" list="kcAbbreviationSearchOptions" autocomplete="off" placeholder="選択または入力">
            </label>
            <label>シーズン検索
              <select id="kcSearchSeason"><option value="">すべて</option>${SEASONS.map((season) => `<option>${season}</option>`).join("")}</select>
            </label>
            <div class="kc-search-actions"><button type="button" class="secondary" id="kcClearSearch">検索をクリア</button></div>
            <datalist id="kcSupplierSearchOptions"></datalist>
            <datalist id="kcYarnNameSearchOptions"></datalist>
            <datalist id="kcAbbreviationSearchOptions"></datalist>
          </div>
          <p id="kcInboxMessage" class="kc-message" role="status">独立Photo Captureの端末内DRAFTを読み込んでいます。</p>
          <div id="kcRecordList"></div>
          <div class="kc-inbox-secondary">
            <details class="kc-usage-details">
              <summary>記録件数・使い方</summary>
              <div class="kc-usage-details-body">
                <div class="kc-kpis" aria-label="Capture summary">
                  <div class="kc-kpi"><span>全レコード</span><strong id="kcKpiRecords">0</strong></div>
                  <div class="kc-kpi"><span>DRAFT</span><strong id="kcKpiDraft">0</strong></div>
                  <div class="kc-kpi"><span>CREATEイベント</span><strong id="kcKpiCreate">0</strong></div>
                  <div class="kc-kpi"><span>UPDATEイベント</span><strong id="kcKpiUpdate">0</strong></div>
                  <div class="kc-kpi"><span>Audit Log</span><strong id="kcKpiAudit">0</strong></div>
                </div>
                <aside class="kc-handoff-guide" aria-label="オーナー版からシステム受信箱への登録手順">
                  <strong>独立版の保存方法</strong>
                  <span>撮影中：端末にDRAFT保存</span><span>引き渡し時：外部取込ZIPを書き出す</span><span>取込後：内容をHuman Reviewで確認</span><span>正式登録：人が確認してから反映</span>
                </aside>
                <aside class="kc-handoff-guide kc-install-guide" aria-label="Androidホーム画面への登録方法">
                  <strong>Androidホーム画面への登録</strong>
                  <span>通常のChromeで開く</span><span>ホーム画面に追加</span><span>アプリをインストール</span><span>KNIT COMPASSロゴを確認</span>
                </aside>
              </div>
            </details>
            <details class="kc-recovery-tools">
              <summary>2.1.41〜2.1.43データを移植</summary>
              <div class="kc-recovery-tools-body">
                <p>Photo Capture 2.1.41〜2.1.43で書き出した外部取込ZIPを選ぶと、写真・履歴・素材情報を独立版の端末内DRAFTへ追加します。原本は変更しません。</p>
                <label class="kc-file-button secondary">2.1.41〜2.1.43 ZIPを取り込む
                  <input class="kc-visually-hidden-file" id="kcPortableImport" type="file" accept=".zip,application/zip" multiple>
                </label>
              </div>
            </details>
          </div>
        </section>

        <section class="kc-editor" id="kcEditor" aria-labelledby="kcEditorTitle" hidden>
          <div class="kc-editor-heading">
            <div>
              <p class="kc-eyebrow">写真・素材情報の入力</p>
              <h2 id="kcEditorTitle">新規キャプチャ</h2>
              <p class="kc-muted">初期状態は必ずDRAFTです。保存済みイベントは上書きしません。</p>
            </div>
            <div class="kc-state-strip" aria-label="登録の流れ">
              <span class="kc-state-chip active">下書き</span>
              <span class="kc-state-chip">内容確認</span>
              <span class="kc-state-chip">正式登録</span>
            </div>
          </div>

          <form id="kcCaptureForm" novalidate>
            <input type="hidden" name="record_id">
            <input type="hidden" name="factory_id">
            <input type="hidden" name="factory_relationship_id">
            <input type="hidden" name="factory_review_status">
            <input type="hidden" name="factory_name_snapshot">
            <input type="hidden" name="data_state" value="DRAFT">
            <input type="hidden" name="human_review_status" value="NOT_REVIEWED">
            <input type="hidden" name="priority" value="NORMAL">
            <input type="hidden" name="legacy_tactile_feelings" value="[]">
            <div class="kc-company-form">
              <section class="kc-form-section" aria-labelledby="kcBasicTitle">
                <h3 id="kcBasicTitle">1. 基本項目</h3>
                <div class="kc-company-form-grid">
                  <label class="kc-company-question">登録日 <span class="kc-required">必須</span>
                    <input name="entry_date" type="date">
                  </label>
                  <label class="kc-company-question">展示会 / 入手先
                    <input name="visit_context" id="kcVisitContextInput" list="kcVisitContextOptions" autocomplete="off" placeholder="展示会・訪問先を選択または入力">
                    <span class="kc-field-hint">展示会を選ぶと、参加する糸・繊維系メーカーへ候補を絞り込みます。</span>
                  </label>
                  <label class="kc-company-question">糸商 / Supplier
                    <input name="supplier" id="kcSupplierInput" list="kcSupplierOptions" autocomplete="off" placeholder="糸商名を選択または入力">
                    <span class="kc-field-hint" id="kcSupplierEventHint">登録済み候補から選択できます。未登録の糸商は直接入力できます。</span>
                  </label>
                  <label class="kc-company-question">糸名・素材名
                    <input name="yarn_name" list="kcYarnNameOptions" autocomplete="off" placeholder="素材名または糸名を入力">
                  </label>
                  <label class="kc-company-question">資料区分
                    <select name="document_type"><option value="">未選択</option><option>カラーBOOK</option><option>編地・スワッチ</option><option>製品サンプル</option><option>原料</option><option>カタログ</option><option>展示会資料</option><option>その他</option></select>
                  </label>
                </div>
              </section>

              <section class="kc-form-section" aria-labelledby="kcPhotoTitle">
                <div class="kc-section-heading">
                  <div><h3 id="kcPhotoTitle">2. 写真 <span class="kc-required">必須</span></h3><p class="kc-muted">7分類で、全分類合計10枚まで追加できます。</p><p class="kc-photo-count" id="kcPhotoCount">0 / 10枚</p></div>
                </div>
                <div class="kc-primary-photo-slot">
                  ${photoSlotTemplate(CAPTURE_PHOTO_TYPES[0], { badge: "撮影箇所" })}
                </div>
                <div class="kc-photo-category-guide">
                  <strong>その他の撮影箇所を追加</strong>
                  <span>必要な分類の「カメラで撮影」または「写真から選択」を押してください。写真は全分類合計10枚までです。</span>
                </div>
                <div class="kc-photo-grid">${CAPTURE_PHOTO_TYPES.slice(1).map((type) => photoSlotTemplate(type, {
                  badge: type.key === "wechat" ? "連絡記録" : "撮影箇所"
                })).join("")}</div>
              </section>

              <section class="kc-form-section" aria-labelledby="kcMaterialTitle">
                <h3 id="kcMaterialTitle">3. 素材項目</h3>
                <div class="kc-company-form-grid">
                  <label class="kc-company-question">番手・規格
                    <input name="yarn_count" autocomplete="off" placeholder="例：2/48NM">
                  </label>
                  <label class="kc-company-question">混率・組成
                    <input name="composition" autocomplete="off" placeholder="例：VIS65 / PET35">
                  </label>
                  <label class="kc-company-question">機能性繊維使用
                    <select name="functional_fiber_usage"><option value="未確認">未確認</option><option>あり</option><option>なし</option></select>
                  </label>
                  <label class="kc-company-question" id="kcFunctionalFiberDetailWrap" hidden>機能性繊維詳細
                    <textarea name="functional_fiber_detail" placeholder="繊維名・機能・確認根拠など"></textarea>
                  </label>
                  <label class="kc-company-question">サステナブル繊維使用
                    <select name="sustainable_fiber_usage"><option value="未確認">未確認</option><option>あり</option><option>なし</option></select>
                  </label>
                  <label class="kc-company-question" id="kcSustainableFiberDetailWrap" hidden>サステナブル繊維詳細
                    <textarea name="sustainable_fiber_detail" placeholder="再生原料、認証、由来など"></textarea>
                  </label>
                  <label class="kc-company-question">シーズン
                    <select name="season"><option value="">未選択</option>${selectOptionsTemplate(SEASONS)}</select>
                  </label>
                  <label class="kc-company-question">糸構造
                    <select name="yarn_structure">${selectOptionsTemplate(YARN_STRUCTURES)}</select>
                  </label>
                  <label class="kc-company-question" id="kcYarnStructureOtherWrap" hidden>糸構造（その他）
                    <input name="yarn_structure_other" autocomplete="off" placeholder="糸構造を入力">
                  </label>
                  <label class="kc-company-question">価格
                    <input name="price" type="number" inputmode="decimal" min="0" step="0.01" autocomplete="off" placeholder="例：38.50">
                  </label>
                  <label class="kc-company-question">通貨
                    <select name="currency">${selectOptionsTemplate(PRICE_CURRENCIES)}</select>
                  </label>
                  <label class="kc-company-question">ゲージ
                    <select name="gauge"><option value="">未選択</option>${selectOptionsTemplate(GAUGES.filter((value) => value !== "未確認"))}</select>
                  </label>
                  <label class="kc-company-question">本取り
                    <input name="knitting_end_count" type="number" inputmode="numeric" min="1" max="20" step="1" autocomplete="off" placeholder="例：2">
                    <span class="kc-field-hint">編立時に一緒に使う糸の本数です。双糸・合撚とは分けて記録します。</span>
                  </label>
                  <label class="kc-company-question">編地組織
                    <select name="knit_structure"><option value="">未選択</option>${selectOptionsTemplate(KNIT_STRUCTURES)}</select>
                  </label>
                  <fieldset class="kc-company-question kc-choice-fieldset">
                    <legend>触感・風合い（複数選択可）</legend>
                    <div class="kc-choice-options kc-company-choice-options">${tactileFeelingTemplate()}</div>
                    <span class="kc-field-hint" id="kcLegacyFeelingStatus"></span>
                  </fieldset>
                  <label class="kc-company-question">メモ
                    <textarea name="notes" placeholder="確認事項、撮影メモ、補足"></textarea>
                  </label>
                </div>
              </section>

              <section class="kc-form-section" aria-labelledby="kcActionTitle">
                <h3 id="kcActionTitle">4. 手配・進捗（任意）</h3>
                <div class="kc-company-form-grid">
                  <label class="kc-company-question">工場設定
                    <input name="factory" list="kcFactoryOptions" autocomplete="off" placeholder="工場名で選択または入力">
                    <span class="kc-factory-control">独立版では工場名を自由入力し、要確認のスナップショットとして保存します。</span>
                    <span id="kcFactoryStatus" class="kc-field-hint" role="status">工場名は端末内DRAFTへ保存されます。</span>
                  </label>
                  <label class="kc-company-question">BOOK手配
                    <select name="book_request"><option>未確認</option><option>手配予定</option><option>手配中</option><option>手配済</option><option>不要</option></select>
                  </label>
                  <label class="kc-company-question">編地手配
                    <select name="fabric_request"><option>未確認</option><option>手配予定</option><option>手配中</option><option>手配済</option><option>不要</option></select>
                  </label>
                  <label class="kc-company-question">手配メモ
                    <textarea name="arrangement_memo" placeholder="色、数量、納期、確認事項など"></textarea>
                  </label>
                </div>
              </section>

              <section class="kc-form-section" aria-labelledby="kcResearchTitle">
                <h3 id="kcResearchTitle">5. 調査依頼（任意）</h3>
                <div class="kc-company-form-grid">
                  <label class="kc-company-question">確認優先度 <span class="kc-required">必須</span>
                    <select name="attention_rating">${selectOptionsTemplate(ATTENTION_RATINGS)}</select>
                  </label>
                  <label class="kc-company-question">糸の調査依頼
                    <select name="research_request"><option>不要</option><option>必要</option></select>
                  </label>
                </div>
              </section>

              <details class="kc-form-section kc-kc-details">
                <summary>Knit Compass補足（任意）</summary>
                <p class="kc-muted">以前のV04下書きに含まれる補足情報を保持し、素材開発画面へ引き継ぎます。</p>
                <div class="kc-form-grid">
                  <label>略称
                    <input name="abbreviation" list="kcAbbreviationOptions" autocomplete="off" placeholder="例：SAY">
                  </label>
                  <label>価格単位
                    <select name="price_unit">${selectOptionsTemplate(PRICE_UNITS)}</select>
                  </label>
                  <fieldset class="kc-choice-fieldset wide"><legend>編成技術（複数選択可）</legend><div class="kc-choice-options">${checkboxOptionsTemplate("knitting_techniques", KNITTING_TECHNIQUES)}</div></fieldset>
                  <label>BOOK掲載状況<select name="book_availability"><option value="">未選択</option>${bookAvailabilityOptionsTemplate()}</select></label>
                  <fieldset class="kc-choice-fieldset wide"><legend>手元にある見本（複数選択）</legend><div class="kc-choice-options">${checkboxOptionsTemplate("sample_status", SAMPLE_STATUS_VALUES)}</div></fieldset>
                  <input type="hidden" name="color_sample" value="">
                  <fieldset class="kc-choice-fieldset wide"><legend>開発アクション（複数選択）</legend><div class="kc-choice-options">${checkboxOptionsTemplate("development_actions", DEVELOPMENT_ACTIONS)}</div></fieldset>
                  <input type="hidden" name="actual_count_structure" data-legacy-technical-field>
                  <select name="spinning_method" hidden><option value="">未確認</option>${spinningMethodOptionsTemplate()}</select>
                  <input type="hidden" name="spinning_method_other" data-legacy-technical-field>
                  <select name="filament_type_observation" hidden><option value="">未確認</option>${filamentTypeOptionsTemplate()}</select>
                  <input type="hidden" name="filament_type_other" data-legacy-technical-field>
                  <select name="composite_structure_observation" hidden><option value="">未選択</option>${selectOptionsTemplate(COMPOSITE_STRUCTURES)}</select>
                  <input type="hidden" name="composite_structure_other" data-legacy-technical-field>
                  <input type="hidden" name="processing_method" data-legacy-technical-field>
                  <select name="covering_structure" hidden data-legacy-technical-field><option value="">未選択</option><option value="SCY">SCY</option><option value="DCY">DCY</option><option value="MONO_FILAMENT">Mono Filament Covering</option><option value="DOUBLE">Double Cover</option><option value="TRIPLE">Triple Cover</option><option value="AIR">Air Cover</option></select>
                  <select name="outer_filament" multiple hidden data-legacy-technical-field><option value="PET_DTY">PET DTY</option><option value="PET_FDY">PET FDY</option><option value="NYLON_DTY">Nylon DTY</option><option value="PBT">PBT</option><option value="ICE_JADE">ICE JADE</option><option value="ASKIN">ASKIN</option><option value="MONO">Mono</option></select>
                </div>
              </details>

              <datalist id="kcVisitContextOptions"></datalist>
              <datalist id="kcSupplierOptions"></datalist>
              <datalist id="kcYarnNameOptions"></datalist>
              <datalist id="kcAbbreviationOptions"></datalist>
              <datalist id="kcFactoryOptions"></datalist>
              <div class="kc-policy" aria-label="保存ルール">
                <div><strong>履歴</strong>変更前の記録も保持</div>
                <div><strong>引渡し</strong>選んだ記録だけZIPを書き出し</div>
                <div><strong>公開</strong>人の確認後に正式登録</div>
              </div>
            </div>
            <p id="kcEditorMessage" class="kc-message" role="status">途中保存は写真または糸情報だけでも可能です。外部取込ZIPを書き出す場合は写真を追加してください。</p>
            <div class="kc-form-actions">
              <button type="button" class="secondary" id="kcCancelEdit">一覧へ戻る</button>
              <button type="submit" class="secondary" id="kcSaveDraft" data-save-destination="LOCAL">端末にDRAFT保存</button>
              <button type="submit" id="kcSaveAndUpload" data-save-destination="INBOX">DRAFT保存＋外部取込ZIP</button>
            </div>
          </form>
        </section>
      </main>`;
  }

  function setMessage(id, text, isError = false) {
    const target = document.getElementById(id);
    if (!target) return;
    target.textContent = text;
    target.classList.toggle("error", isError);
  }

  function updateConnectivityStatus(announce = false) {
    state.isOnline = typeof navigator === "undefined" ? true : navigator.onLine !== false;
    const status = document.getElementById("kcConnectivityStatus");
    const label = document.getElementById("kcConnectivityLabel");
    const detail = document.getElementById("kcConnectivityDetail");
    if (status) status.dataset.connectivity = state.isOnline ? "online" : "offline";
    if (label) label.textContent = state.isOnline ? "独立版｜通信あり" : "独立版｜オフライン";
    if (detail) detail.textContent = "DRAFT保存と外部取込ZIPの書き出しは、この端末だけで利用できます。";
    updateSaveButtonState();
    if (announce) {
      setMessage(
        "kcInboxMessage",
        state.isOnline ? "通信が戻りました。端末内DRAFTはそのまま利用できます。" : "オフラインです。入力中の内容とDRAFTは端末内に保持されます。",
        false
      );
    }
  }

  function loadDeviceSession() {
    try {
      const stored = JSON.parse(sessionStorage.getItem(SESSION_KEY) || "null");
      return stored?.accountId ? stored : null;
    } catch {
      return null;
    }
  }

  async function ensureImmediateDeviceSession() {
    const accounts = await getAll(STORES.accounts);
    if (accounts.length > 1) return null;

    let account = accounts[0] || null;
    if (!account) {
      const salt = crypto.getRandomValues(new Uint8Array(16));
      const deviceSecretHash = [...crypto.getRandomValues(new Uint8Array(32))]
        .map((byte) => byte.toString(16).padStart(2, "0"))
        .join("");
      account = {
        accountId: generatedAccountId(),
        displayName: "Photo Capture利用者",
        salt: [...salt],
        passHash: deviceSecretHash,
        iterations: 0,
        deviceAutoUnlock: true
      };
      const transaction = state.db.transaction(STORES.accounts, "readwrite");
      transaction.objectStore(STORES.accounts).add(account);
      await transactionPromise(transaction);
      window.KnitCompassBackup?.notifyDataChanged?.();
    }

    const session = {
      accountId: account.accountId,
      displayName: account.displayName || "Photo Capture利用者",
      realm: CONTRACT.authentication_realm
    };
    sessionStorage.setItem(SESSION_KEY, JSON.stringify(session));
    return session;
  }

  async function renderDeviceAuth() {
    const accounts = await getAll(STORES.accounts);
    const hasAccount = accounts.length > 0;
    const accountChoice = accounts.length > 1
      ? `<label>利用者<select name="account" required>${accounts.map((account) => `<option value="${escapeHtml(account.accountId)}">${escapeHtml(account.displayName || "保存済み利用者")}</option>`).join("")}</select></label>`
      : "";
    const guidance = !hasAccount
      ? "初回利用です。表示名とパスフレーズを設定してください。"
      : accounts.length === 1
        ? `${escapeHtml(accounts[0].displayName || "保存済み利用者")}の端末内DRAFTを開きます。`
        : "利用者を選び、パスフレーズを入力してください。";
    app.innerHTML = `
      <main class="kc-app kc-auth-wrap">
        <section class="kc-auth-card" aria-labelledby="kcAuthTitle">
          <p class="kc-eyebrow">独立Photo Capture</p>
          <h1 id="kcAuthTitle">Knit Compass Photo Capture</h1>
          <p class="kc-lead">2.1.43の入力画面を独立版へ移植しました。写真とDRAFTはこの端末内に保存され、外部へ自動送信しません。</p>
          <div class="kc-badges" aria-label="データ保護方針"><span class="kc-badge safe">端末内保存</span><span class="kc-badge safe">Append Only</span><span class="kc-badge">正式登録は人が確認</span></div>
          <form id="auth" class="kc-auth-form">
            ${hasAccount ? "" : `<label>表示名<input name="display" required placeholder="例：Knit Compass Owner"></label>`}
            ${accountChoice}
            <label>パスフレーズ<input name="pass" type="password" minlength="10" required><small>10文字以上。メールアドレスは不要です。</small></label>
            <button type="submit">${hasAccount ? "保存データを開く" : "利用を開始"}</button>
          </form>
          <p id="kcAuthMessage" class="kc-message" role="status">${guidance}</p>
        </section>
      </main>`;

    document.getElementById("auth").addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = event.currentTarget;
      const password = form.elements.pass.value;
      const message = document.getElementById("kcAuthMessage");
      try {
        let account = hasAccount
          ? (accounts.length === 1 ? accounts[0] : accounts.find((row) => row.accountId === form.elements.account.value))
          : null;
        if (!hasAccount) {
          const displayName = clean(form.elements.display.value);
          if (!displayName) throw new Error("表示名を入力してください");
          const salt = crypto.getRandomValues(new Uint8Array(16));
          account = {
            accountId: generatedAccountId(),
            displayName,
            salt: [...salt],
            passHash: await passwordHash(password, salt),
            iterations: 180000
          };
          const transaction = state.db.transaction(STORES.accounts, "readwrite");
          transaction.objectStore(STORES.accounts).add(account);
          await transactionPromise(transaction);
          window.KnitCompassBackup?.notifyDataChanged?.();
        } else if (!account || await passwordHash(password, new Uint8Array(account.salt), account.iterations) !== account.passHash) {
          throw new Error("パスフレーズが違います");
        }
        state.session = { accountId: account.accountId, displayName: account.displayName, realm: CONTRACT.authentication_realm };
        sessionStorage.setItem(SESSION_KEY, JSON.stringify(state.session));
        await renderApplication();
      } catch (error) {
        message.textContent = `認証できませんでした: ${error.message || error}`;
        message.classList.add("error");
      }
    });
  }

  function revokeObjectUrls() {
    state.objectUrls.forEach((url) => URL.revokeObjectURL(url));
    state.objectUrls.clear();
  }

  function normalizeStandaloneSnapshot(snapshot = {}) {
    const documentTypes = {
      color_book: "カラーBOOK",
      swatch: "編地・スワッチ",
      product_sample: "製品サンプル",
      raw_material: "原料",
      catalog: "カタログ",
      exhibition: "展示会資料",
      other: "その他"
    };
    const functionItems = Array.isArray(snapshot.functionalProperties) ? snapshot.functionalProperties : [];
    const sustainableItems = Array.isArray(snapshot.sustainableAttributes) ? snapshot.sustainableAttributes : [];
    return {
      ...snapshot,
      entryDate: clean(snapshot.entryDate || snapshot.captureDate) || todayJst(),
      documentType: documentTypes[clean(snapshot.documentType)] || documentTypeForEditor(snapshot.documentType),
      visitContext: clean(snapshot.visitContext || snapshot.acquisitionSource),
      supplier: clean(snapshot.supplier || snapshot.sourceOrganizationName),
      yarnName: clean(snapshot.yarnName || snapshot.materialName),
      abbreviation: clean(snapshot.abbreviation || snapshot.yarnCode),
      yarnCount: clean(snapshot.yarnCount || snapshot.countDisplay || snapshot.countValue),
      composition: clean(snapshot.composition || snapshot.compositionRaw),
      knittingEndCount: normalizeKnittingEndCount(snapshot.knittingEndCount || snapshot.knittingEnds),
      functionalFiberUsage: clean(snapshot.functionalFiberUsage) || (functionItems.length ? "あり" : "未確認"),
      functionalFiberDetail: clean(snapshot.functionalFiberDetail || snapshot.functionDetail),
      sustainableFiberUsage: clean(snapshot.sustainableFiberUsage) || (sustainableItems.length ? "あり" : "未確認"),
      sustainableFiberDetail: clean(snapshot.sustainableFiberDetail || snapshot.sustainableBasis),
      seasons: seasonsForEditor((snapshot.seasons || []).map((season) => season === "通年" ? "シーズンレス" : season)),
      photoRefs: Array.isArray(snapshot.photoRefs) ? snapshot.photoRefs : []
    };
  }

  async function loadEvents() {
    state.events = (await getAll(STORES.events)).map((event) => ({
      ...event,
      snapshot: normalizeStandaloneSnapshot(event.snapshot)
    })).sort((left, right) => {
      if (left.recordId === right.recordId) return left.version - right.version;
      return left.createdAt.localeCompare(right.createdAt);
    });
    const latest = new Map();
    state.events.forEach((event) => {
      const current = latest.get(event.recordId);
      if (!current || event.version > current.version) latest.set(event.recordId, event);
    });
    state.latestRecords = [...latest.values()].sort((left, right) => right.updatedAt.localeCompare(left.updatedAt));
  }

  function selectedValues(select) {
    return [...select.selectedOptions].map((option) => option.value).filter(Boolean);
  }

  function fillDatalist(id, values) {
    const target = document.getElementById(id);
    if (!target) return;
    const unique = [...new Set(values.map(clean).filter(Boolean))].sort((a, b) => a.localeCompare(b, "ja"));
    target.innerHTML = unique.map((value) => `<option value="${escapeHtml(value)}"></option>`).join("");
  }

  function fillSupplierDatalist(id, supplierRecords, fallbackValues = []) {
    const target = document.getElementById(id);
    if (!target) return;
    const options = new Map();
    supplierRecords.forEach((supplier) => {
      const value = clean(supplier.name_en || supplier.display_name || supplier.name_zh);
      if (!value) return;
      options.set(normalizedLookup(value), {
        value,
        label: clean(supplier.name_zh) || clean(supplier.display_name)
      });
    });
    fallbackValues.map(clean).filter(Boolean).forEach((value) => {
      const lookup = normalizedLookup(value);
      if (!options.has(lookup)) options.set(lookup, { value, label: "" });
    });
    target.innerHTML = [...options.values()]
      .sort((left, right) => left.value.localeCompare(right.value, "en"))
      .map((option) => `<option value="${escapeHtml(option.value)}"${option.label ? ` label="${escapeHtml(option.label)}"` : ""}></option>`)
      .join("");
  }

  function refreshSupplierOptionsForVisitContext() {
    const visitInput = document.getElementById("kcVisitContextInput");
    const hint = document.getElementById("kcSupplierEventHint");
    const event = exhibitionForVisitContext(visitInput?.value);
    const historicalSuppliers = state.latestRecords.map((item) => item.snapshot.supplier);
    const allEventSuppliers = EXHIBITION_EVENTS.flatMap((item) => exhibitionSupplierCandidates(item));
    if (event) {
      const eventSuppliers = exhibitionSupplierCandidates(event);
      fillSupplierDatalist("kcSupplierOptions", eventSuppliers);
      if (hint) {
        hint.textContent = `${event.label}の糸・繊維系出展者 ${eventSuppliers.length}社から選択できます。糸・繊維系以外は除外し、未登録の糸商は直接入力できます。`;
      }
      return;
    }
    fillSupplierDatalist("kcSupplierOptions", allEventSuppliers, [
      ...(state.masters.supplier || []),
      ...historicalSuppliers
    ]);
    if (hint) {
      hint.textContent = "登録済み候補から選択できます。入手経路で展示会を選ぶと参加糸商に絞り込まれ、未登録の糸商は直接入力できます。";
    }
  }

  function refreshCandidateOptions() {
    const fields = state.latestRecords.map((event) => event.snapshot);
    const visitContext = [...ACQUISITION_SOURCE_OPTIONS, ...fields.map((row) => row.visitContext)];
    const allEventSuppliers = EXHIBITION_EVENTS.flatMap((event) => exhibitionSupplierCandidates(event));
    const yarnName = [...(state.masters.yarn_name || []), ...fields.map((row) => row.yarnName)];
    const abbreviation = [...(state.masters.abbreviation || []), ...fields.map((row) => row.abbreviation)];
    fillSupplierDatalist("kcSupplierSearchOptions", allEventSuppliers, [
      ...(state.masters.supplier || []),
      ...fields.map((row) => row.supplier)
    ]);
    ["kcYarnNameOptions", "kcYarnNameSearchOptions"].forEach((id) => fillDatalist(id, yarnName));
    ["kcAbbreviationOptions", "kcAbbreviationSearchOptions"].forEach((id) => fillDatalist(id, abbreviation));
    fillDatalist("kcVisitContextOptions", visitContext);
    refreshSupplierOptionsForVisitContext();
  }

  function filteredRecords() {
    const contains = (value, term) => !term || clean(value).toLocaleLowerCase().includes(clean(term).toLocaleLowerCase());
    return state.latestRecords.filter((event) => {
      const row = event.snapshot;
      const searchable = [
        event.recordId, row.documentType, row.visitContext, row.supplier, row.yarnName, row.factory, row.abbreviation,
        row.yarnCount, row.qualityLabel, row.specificationText, row.yarnStructure, row.composition, row.gauge, row.knitStructure, row.actualCountStructure,
        row.arrangementMemo, row.notes, ...(row.seasons || []), ...(row.tactileFeelings || [])
      ].join(" ");
      return contains(searchable, state.filters.query)
        && contains(row.supplier, state.filters.supplier)
        && contains(row.yarnName, state.filters.yarnName)
        && contains(row.abbreviation, state.filters.abbreviation)
        && (!state.filters.season || (row.seasons || []).includes(state.filters.season));
    });
  }

  function normalizeRotation(value) {
    return ((Number(value) % 360) + 360) % 360;
  }

  function orientationLabel(width, height) {
    if (!width || !height) return "UNKNOWN";
    if (width === height) return "SQUARE";
    return width > height ? "LANDSCAPE" : "PORTRAIT";
  }

  function captureFileName(extension = "jpg") {
    const now = new Date();
    const pad = (value) => String(value).padStart(2, "0");
    const stamp = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}_${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    return `KC_PC_${stamp}_${crypto.randomUUID().slice(0, 4).toUpperCase()}.${extension}`;
  }

  async function readExifOrientation(file) {
    if (!file || !/jpe?g/i.test(file.type || file.name || "")) return null;
    try {
      const buffer = await file.slice(0, 262144).arrayBuffer();
      const view = new DataView(buffer);
      if (view.byteLength < 4 || view.getUint16(0, false) !== 0xFFD8) return null;
      let offset = 2;
      while (offset + 4 <= view.byteLength) {
        const marker = view.getUint16(offset, false);
        offset += 2;
        if ((marker & 0xFF00) !== 0xFF00) break;
        if (marker === 0xFFDA || marker === 0xFFD9) break;
        const length = view.getUint16(offset, false);
        if (length < 2 || offset + length > view.byteLength) break;
        if (marker === 0xFFE1 && length >= 10 && view.getUint32(offset + 2, false) === 0x45786966) {
          const tiff = offset + 8;
          const little = view.getUint16(tiff, false) === 0x4949;
          const get16 = (pos) => view.getUint16(pos, little);
          const get32 = (pos) => view.getUint32(pos, little);
          const ifd = tiff + get32(tiff + 4);
          if (ifd + 2 > view.byteLength) return null;
          const entries = get16(ifd);
          for (let index = 0; index < entries; index += 1) {
            const entry = ifd + 2 + index * 12;
            if (entry + 12 > view.byteLength) break;
            if (get16(entry) === 0x0112) return get16(entry + 8);
          }
          return null;
        }
        offset += length;
      }
    } catch {
      return null;
    }
    return null;
  }

  async function decodeImageSource(file) {
    if ("createImageBitmap" in window) {
      try {
        const bitmap = await createImageBitmap(file, { imageOrientation: "from-image", colorSpaceConversion: "default" });
        return { source: bitmap, width: bitmap.width, height: bitmap.height, close: () => bitmap.close?.() };
      } catch {
        // Fall through to HTMLImageElement for browser compatibility.
      }
    }
    const url = URL.createObjectURL(file);
    try {
      const image = new Image();
      image.decoding = "async";
      image.src = url;
      await image.decode();
      return { source: image, width: image.naturalWidth, height: image.naturalHeight, close: () => undefined };
    } finally {
      URL.revokeObjectURL(url);
    }
  }

  function canvasContext(canvas) {
    let context = null;
    try {
      context = canvas.getContext("2d", { alpha: false, colorSpace: "display-p3" });
    } catch {
      context = null;
    }
    return context || canvas.getContext("2d", { alpha: false });
  }

  function canvasBlob(canvas, mediaType, quality) {
    return new Promise((resolve, reject) => {
      canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error("PHOTO_ENCODE_FAILED")), mediaType, quality);
    });
  }

  async function processImageFile(originalFile, options = {}) {
    if (!originalFile || !String(originalFile.type || "").startsWith("image/")) throw new Error("IMAGE_FILE_REQUIRED");
    const manualRotationDegree = normalizeRotation(options.manualRotationDegree || 0);
    const decoded = await decodeImageSource(originalFile);
    const maxLongEdge = 4096;
    const scale = Math.min(1, maxLongEdge / Math.max(decoded.width, decoded.height));
    const sourceWidth = Math.max(1, Math.round(decoded.width * scale));
    const sourceHeight = Math.max(1, Math.round(decoded.height * scale));
    const quarterTurn = manualRotationDegree === 90 || manualRotationDegree === 270;
    const canvas = document.createElement("canvas");
    canvas.width = quarterTurn ? sourceHeight : sourceWidth;
    canvas.height = quarterTurn ? sourceWidth : sourceHeight;
    const context = canvasContext(canvas);
    if (!context) {
      decoded.close();
      throw new Error("CANVAS_CONTEXT_UNAVAILABLE");
    }
    context.imageSmoothingEnabled = true;
    context.imageSmoothingQuality = "high";
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.translate(canvas.width / 2, canvas.height / 2);
    context.rotate(manualRotationDegree * Math.PI / 180);
    context.drawImage(decoded.source, -sourceWidth / 2, -sourceHeight / 2, sourceWidth, sourceHeight);
    decoded.close();

    const mediaType = originalFile.type === "image/png" ? "image/png" : "image/jpeg";
    const extension = mediaType === "image/png" ? "png" : "jpg";
    const blob = await canvasBlob(canvas, mediaType, mediaType === "image/jpeg" ? 0.96 : undefined);
    const fileName = options.fileName || captureFileName(extension);
    const file = new File([blob], fileName, { type: mediaType, lastModified: Date.now() });
    const exifOrientation = await readExifOrientation(originalFile);
    return {
      file,
      originalFile,
      sourceMode: options.sourceMode || "unknown",
      manualRotationDegree,
      exifOrientation,
      originalWidth: decoded.width,
      originalHeight: decoded.height,
      width: canvas.width,
      height: canvas.height,
      resized: scale < 1,
      orientationOriginal: orientationLabel(decoded.width, decoded.height),
      orientationFinal: orientationLabel(canvas.width, canvas.height),
      orientationNormalized: true,
      normalizedAt: isoNow()
    };
  }

  function photoStatusText(entry) {
    const exif = entry.exifOrientation == null ? "EXIF不明" : `EXIF ${entry.exifOrientation}`;
    const resized = entry.resized ? " / 長辺4096pxへ縮小" : "";
    return `${entry.width}×${entry.height} / ${entry.orientationFinal} / ${exif} / 方向正規化済み${resized}`;
  }

  function photoPreviewMarkup(type, entry, mode = "pending") {
    const label = photoTypeDefinition(type).label;
    const entryId = entry.clientPhotoId || type;
    const url = URL.createObjectURL(entry.file);
    state.objectUrls.add(url);
    const portrait = entry.orientationFinal === "PORTRAIT";
    return `
      <div class="kc-photo-stage"><img src="${escapeHtml(url)}" alt="${escapeHtml(label)}プレビュー"></div>
      <figcaption>${mode === "existing" ? "保存済み写真を補正用に読込み" : "補正済み"} / ${escapeHtml(entry.file.name)}</figcaption>
      <div class="kc-photo-status ${portrait ? "warning" : "safe"}" data-photo-orientation-status="${escapeHtml(entryId)}">
        ${escapeHtml(photoStatusText(entry))}${portrait ? "。縦向きです。糸帳・編地は横向き撮影を推奨します。" : ""}
      </div>
      <div class="kc-photo-tools" aria-label="${escapeHtml(label)}の向き補正">
        <button type="button" class="secondary" data-photo-rotate="90" data-photo-entry="${escapeHtml(entryId)}">写真を90°回転</button>
        <button type="button" data-photo-download="${escapeHtml(entryId)}">端末に保存</button>
        <button type="button" class="ghost" data-photo-remove="${escapeHtml(entryId)}">選択を解除</button>
      </div>`;
  }

  function triggerFileDownload(file) {
    const url = URL.createObjectURL(file);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = file.name || captureFileName("jpg");
    anchor.rel = "noopener";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  function updateSaveButtonState() {
    const localButton = document.getElementById("kcSaveDraft");
    const inboxButton = document.getElementById("kcSaveAndUpload");
    if (!localButton || !inboxButton) return;
    const disabled = state.isSaving || state.processingPhotos.size > 0;
    localButton.disabled = disabled;
    inboxButton.disabled = disabled;
    if (state.processingPhotos.size > 0) {
      localButton.textContent = "写真を補正中...";
      inboxButton.textContent = "写真を補正中...";
    } else if (state.isSaving) {
      localButton.textContent = state.saveDestination === "LOCAL" ? "端末へ保存中…" : "処理中…";
      inboxButton.textContent = state.saveDestination === "INBOX" ? "DRAFT保存・ZIP作成中…" : "処理中…";
    } else if (state.editingRecordId) {
      localButton.textContent = "UPDATEを端末保存";
      inboxButton.textContent = "UPDATE保存＋外部取込ZIP";
    } else {
      localButton.textContent = "端末にDRAFT保存";
      inboxButton.textContent = "DRAFT保存＋外部取込ZIP";
    }
  }

  function setPhotoProcessing(type, active) {
    if (active) state.processingPhotos.add(type);
    else state.processingPhotos.delete(type);
    updateSaveButtonState();
  }

  function photoGalleryTemplate(refs) {
    const ordered = sortPhotoEntries(refs || []).slice(0, MAX_PHOTOS_PER_RECORD);
    if (!ordered.length) return `<div class="kc-photo-placeholder">写真未登録</div>`;
    return ordered.map((ref) => `<figure><div class="kc-photo-placeholder" data-record-photo="${escapeHtml(ref.photoId)}">読込中...</div><figcaption>${escapeHtml(ref.label || photoTypeDefinition(ref.type).label)}</figcaption></figure>`).join("");
  }

  function detailTemplate(event) {
    const row = event.snapshot;
    const detailRows = [
      ["Capture ID", event.recordId],
      ["登録日", row.entryDate || "—"],
      ["資料分類", row.documentType || "—"],
      ["入手経路", row.visitContext || "—"],
      ["展示会ID", row.sourceEventId || "—"],
      ["Supplier", row.supplier || "—"],
      ["糸商マスターID", row.supplierMasterId || "—"],
      ["糸名・素材名", row.yarnName || "—"],
      ["設定工場", row.factory || "—"],
      ["工場ID", row.factoryId || "未接続"],
      ["工場取引関係", row.factoryRelationshipId || "未接続"],
      ["工場確認状態", row.factoryReviewStatus || (row.factory ? "REVIEW_REQUIRED" : "—")],
      ["撮影時工場名", row.factoryNameSnapshot || row.factory || "—"],
      ["略称", row.abbreviation || "—"],
      ["番手", row.yarnCount || "—"],
      ["混率", row.composition || "—"],
      ["品質表示", row.qualityLabel || "—"],
      ["規格", row.specificationText || "—"],
      ["糸構造", row.yarnStructure || "—"],
      ["価格", row.price ? `${row.price} ${row.currency || "通貨未確認"}${row.priceUnit ? `/${row.priceUnit}` : "／単位未確認"}` : "—"],
      ["対応ゲージ（目安）", gaugeRange(row.gaugeMin, row.gaugeMax, row.gauge).label || "—"],
      ["本取り", row.knittingEndCount ? `${row.knittingEndCount}本取り` : "—"],
      ["編地組織", row.knitStructure || "—"],
      ["編成技術", (row.knittingTechniques || []).join(" / ") || "—"],
      ["BOOK掲載状況", bookAvailabilityLabel(row.bookAvailability) || "—"],
      ["手元にある見本", sampleStatusForEditor(row.sampleStatus, row.colorSample).join(" / ") || "—"],
      ["触感・風合い", (row.tactileFeelings || []).join(" / ") || "—"],
      ["重要度", row.attentionRating || companyImportance(row.priority) || "—"],
      ["開発アクション", (row.developmentActions || []).join(" / ") || "—"],
      ["機能性繊維使用", row.functionalFiberUsage || "—"],
      ["機能性繊維詳細", row.functionalFiberDetail || "—"],
      ["サステナブル繊維使用", row.sustainableFiberUsage || "—"],
      ["サステナブル繊維詳細", row.sustainableFiberDetail || "—"],
      ["実番手・構造", row.actualCountStructure || "—"],
      ["精紡方式（仮入力）", row.spinningMethod || "—"],
      ["精紡方式その他補足", row.spinningMethodOther || "—"],
      ["フィラメント種類", row.filamentTypeObservation || "—"],
      ["フィラメント種類その他補足", row.filamentTypeOther || "—"],
      ["複合構造", row.compositeStructureObservation || "—"],
      ["複合構造その他補足", row.compositeStructureOther || "—"],
      ["加工方法", row.processingMethod || "—"],
      ["カバリング構造", row.coveringStructure || "—"],
      ["外層フィラメント", (row.outerFilament || []).join(" / ") || "—"],
      ["シーズン", (row.seasons || []).join(" / ") || "—"],
      ["BOOK手配", row.bookRequest || "—"],
      ["編地手配", row.fabricRequest || "—"],
      ["手配メモ", row.arrangementMemo || "—"],
      ["糸の調査依頼", row.researchRequest || "—"],
      ["Human Review", event.humanReviewStatus],
      ["元写真ID", (event.originalPhotoIds || []).join(" / ") || "—"],
      ["登録日時", formatDate(event.createdAt)],
      ["更新日時", formatDate(event.updatedAt)],
      ["イベント", `${event.eventType} / Version ${event.version}`],
      ["メモ", row.notes || "—"]
    ];
    return `<dl>${detailRows.map(([key, value]) => `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd>`).join("")}</dl>`;
  }

  function renderRecords() {
    const list = document.getElementById("kcRecordList");
    if (!list) return;
    const rows = filteredRecords();
    document.getElementById("kcKpiRecords").textContent = String(state.latestRecords.length);
    document.getElementById("kcKpiDraft").textContent = String(state.latestRecords.filter((event) => event.dataState === "DRAFT").length);
    document.getElementById("kcKpiCreate").textContent = String(state.events.filter((event) => event.eventType === "CREATE").length);
    document.getElementById("kcKpiUpdate").textContent = String(state.events.filter((event) => event.eventType === "UPDATE").length);
    document.getElementById("kcKpiAudit").textContent = String(state.events.length);
    updateConnectivityStatus();

    if (state.latestRecords.length === 0) {
      list.innerHTML = `<div class="kc-empty"><div><strong>まだキャプチャはありません</strong><p>「新しい素材を撮影・登録」から、最初のDRAFTを追加してください。必要な記録は外部取込ZIPとして引き渡せます。</p><button type="button" data-empty-create>最初のDRAFTを作成</button></div></div>`;
      setMessage("kcInboxMessage", "保存済みDRAFTは0件です。");
      return;
    }
    if (rows.length === 0) {
      list.innerHTML = `<div class="kc-empty"><div><strong>条件に一致するデータがありません</strong><p>検索条件を変更するか、検索をクリアしてください。</p><button type="button" class="secondary" data-empty-clear>検索をクリア</button></div></div>`;
      setMessage("kcInboxMessage", `保存済み${state.latestRecords.length}件 / 検索結果0件。`);
      return;
    }
    list.innerHTML = `<div class="kc-record-list">${rows.map((event) => {
      const row = event.snapshot;
      return `
        <article class="kc-record">
          <div class="kc-record-heading">
            <div><h3>${escapeHtml(row.yarnName || "名称未入力のDRAFT")}</h3><p>${escapeHtml(row.supplier || "Supplier未入力")} / ${escapeHtml(row.abbreviation || "略称未入力")}</p></div>
            <span class="kc-priority">${escapeHtml(row.attentionRating || companyImportance(row.priority))}</span>
          </div>
          <div class="kc-material-specs" aria-label="素材の主要規格">
            <span><small>番手</small><strong>${escapeHtml(row.yarnCount || "未入力")}</strong></span>
            <span><small>混率</small><strong>${escapeHtml(row.composition || "未入力")}</strong></span>
            <span><small>品質表示・規格</small><strong>${escapeHtml([row.qualityLabel, row.specificationText].map(clean).filter(Boolean).join(" / ") || "未入力")}</strong></span>
            <span><small>ゲージ × 本取り</small><strong>${escapeHtml(knittingSpecificationLabel(gaugeRange(row.gaugeMin, row.gaugeMax, row.gauge).label, row.knittingEndCount) || "未入力")}</strong></span>
          </div>
          <div class="kc-record-gallery">${photoGalleryTemplate(row.photoRefs)}</div>
          <div class="kc-record-meta"><span>${escapeHtml(event.dataState)}</span><span>${escapeHtml(event.eventType)} v${event.version}</span><span>${escapeHtml(formatDate(event.updatedAt))}</span></div>
          <div class="kc-record-actions">
            <button type="button" class="portable-export" data-portable-export="${escapeHtml(event.recordId)}" ${state.exportingRecords.has(event.recordId) ? "disabled" : ""}>${state.exportingRecords.has(event.recordId) ? "ZIP作成中..." : "外部取込ZIPを書き出す"}</button>
            <button type="button" class="secondary" data-detail="${escapeHtml(event.recordId)}" aria-expanded="false">保存内容を表示</button>
            <button type="button" data-edit="${escapeHtml(event.recordId)}">編集・再保存</button>
          </div>
          <div class="kc-detail" data-detail-panel="${escapeHtml(event.recordId)}" hidden>${detailTemplate(event)}</div>
        </article>`;
    }).join("")}</div>`;
    setMessage("kcInboxMessage", `保存済み${state.latestRecords.length}件 / 検索結果${rows.length}件。最新値を表示しています。`);
    hydrateRecordPhotos();
  }

  async function loadPhoto(photoId) {
    const record = await getOne(STORES.photos, photoId);
    if (!record?.blob) return null;
    const url = URL.createObjectURL(record.blob);
    state.objectUrls.add(url);
    return { url, record };
  }

  async function hydrateRecordPhotos() {
    const placeholders = [...document.querySelectorAll("[data-record-photo]")];
    await Promise.all(placeholders.map(async (placeholder) => {
      const loaded = await loadPhoto(placeholder.dataset.recordPhoto);
      if (!loaded || !placeholder.isConnected) return;
      const image = document.createElement("img");
      image.src = loaded.url;
      image.alt = loaded.record.label || "保存済み写真";
      image.addEventListener("error", () => {
        image.replaceWith(Object.assign(document.createElement("div"), { className: "kc-photo-placeholder", textContent: "写真を表示できません" }));
      }, { once: true });
      placeholder.replaceWith(image);
    }));
  }

  function existingPhotoPreviewMarkup(type, loaded, existing) {
    return `
      <div class="kc-photo-stage"><img src="${escapeHtml(loaded.url)}" alt="${escapeHtml(type.label)}"></div>
      <p class="kc-photo-item-label">${escapeHtml(existing.label || type.label)}</p>
      <figcaption>保存済み / ${escapeHtml(existing.fileName || type.label)}</figcaption>
      <div class="kc-photo-status">保存済み画像です。回転すると補正済みの新しい写真としてUPDATEに追加されます。</div>
      <div class="kc-photo-tools" aria-label="保存済み写真の向き補正">
        <button type="button" class="secondary" data-photo-rotate-existing="90" data-photo-id="${escapeHtml(existing.photoId)}">写真を90°回転</button>
        <button type="button" data-photo-download-existing="${escapeHtml(existing.photoId)}">補正して端末保存</button>
        <button type="button" class="ghost" data-photo-remove-existing="${escapeHtml(existing.photoId)}">この写真を外す</button>
      </div>`;
  }

  async function renderEditorPhotoPreviews() {
    const replacements = new Set([...state.pendingFiles.values()].map((entry) => entry.replacesPhotoId).filter(Boolean));
    for (const type of PHOTO_TYPES) {
      const preview = document.querySelector(`[data-photo-preview="${type.key}"]`);
      if (!preview) continue;
      const existing = state.existingPhotoRefs.filter((ref) => displayCategoryForType(ref.type) === type.key && !state.removedPhotoIds.has(ref.photoId) && !replacements.has(ref.photoId));
      const pending = [...state.pendingFiles.values()].filter((entry) => displayCategoryForType(entry.type) === type.key);
      if (!existing.length && !pending.length) {
        preview.innerHTML = `<div class="kc-photo-placeholder">写真はまだ選択されていません</div>`;
        continue;
      }
      preview.innerHTML = `<div class="kc-photo-collection">${existing.map((ref) => `<article class="kc-photo-item"><div class="kc-photo-placeholder" data-editor-photo="${escapeHtml(ref.photoId)}">保存済み写真を読込中...</div></article>`).join("")}${pending.map((entry) => `<article class="kc-photo-item">${photoPreviewMarkup(entry.type, entry, entry.replacesPhotoId ? "existing" : "pending")}</article>`).join("")}</div>`;
      await Promise.all(existing.map(async (ref) => {
        const placeholder = preview.querySelector(`[data-editor-photo="${CSS.escape(ref.photoId)}"]`);
        const loaded = await loadPhoto(ref.photoId);
        if (!loaded || !placeholder?.isConnected) return;
        placeholder.parentElement.innerHTML = existingPhotoPreviewMarkup(photoTypeDefinition(ref.type), loaded, ref);
      }));
    }
    const count = document.getElementById("kcPhotoCount");
    if (count) count.textContent = `${activePhotoCount()} / ${MAX_PHOTOS_PER_RECORD}枚`;
  }

  function setSelected(select, values) {
    const selected = new Set(Array.isArray(values) ? values : []);
    [...select.options].forEach((option) => { option.selected = selected.has(option.value); });
  }

  function setSelectValuePreserving(select, value) {
    const current = clean(value);
    if (!current) {
      select.value = "";
      return;
    }
    if (![...select.options].some((option) => option.value === current)) {
      const option = document.createElement("option");
      option.value = current;
      option.textContent = `${current}（旧データ）`;
      select.appendChild(option);
    }
    select.value = current;
  }

  function setChecked(elements, values) {
    const selected = new Set(Array.isArray(values) ? values : []);
    [...elements].forEach((checkbox) => { checkbox.checked = selected.has(checkbox.value); });
  }

  function renderCompanyFactoryOptions() {
    const target = document.getElementById("kcFactoryOptions");
    if (!target) return;
    target.innerHTML = state.companyFactories
      .map((factory) => `<option value="${escapeHtml(factory.factory_name)}">${escapeHtml([factory.country_region, ...(factory.production_stages || [])].filter(Boolean).join(" / "))}</option>`)
      .join("");
  }

  function syncFactorySelection({ preserveStored = false } = {}) {
    const form = document.getElementById("kcCaptureForm");
    if (!form) return;
    const enteredName = clean(form.elements.factory.value);
    const status = document.getElementById("kcFactoryStatus");
    const candidateButton = document.getElementById("kcRegisterFactoryCandidate");
    const exact = state.companyFactories.find((factory) => normalizedFactoryName(factory.factory_name) === normalizedFactoryName(enteredName));
    if (exact) {
      form.elements.factory_id.value = clean(exact.factory_id);
      form.elements.factory_relationship_id.value = clean(exact.relationship_id);
      form.elements.factory_review_status.value = clean(exact.review_status || "REVIEW_REQUIRED");
      form.elements.factory_name_snapshot.value = enteredName || clean(exact.factory_name);
      status.textContent = exact.review_status === "CONFIRMED"
        ? `会社の工場リストに接続済み（${exact.factory_id}）`
        : "会社の工場候補に接続済み。管理者の確認待ちです。";
      if (candidateButton) candidateButton.hidden = true;
      return;
    }
    if (!preserveStored || !enteredName) {
      form.elements.factory_id.value = "";
      form.elements.factory_relationship_id.value = "";
    }
    form.elements.factory_review_status.value = enteredName ? "REVIEW_REQUIRED" : "";
    form.elements.factory_name_snapshot.value = enteredName;
    if (!enteredName) {
      status.textContent = state.companyFactoriesLoaded
        ? "工場名を会社の工場リストから選択できます。"
        : "工場リスト未接続。自由入力と端末保存はそのまま使えます。";
      if (candidateButton) candidateButton.hidden = true;
      return;
    }
    status.textContent = state.companyFactoriesLoaded
      ? "会社の工場リストにない名称です。保存時は要確認として記録します。"
      : "自由入力の工場名を、要確認スナップショットとして端末に保存します。";
    if (candidateButton) candidateButton.hidden = !state.companyFactoriesLoaded;
  }

  async function loadCompanyFactories() {
    const bridge = window.KC_PHOTO_CAPTURE_FACTORY_BRIDGE;
    if (!bridge) throw new Error("FACTORY_BRIDGE_UNAVAILABLE");
    const factories = await bridge.listFactories();
    state.companyFactories = Array.isArray(factories) ? factories : [];
    state.companyFactoriesLoaded = true;
    renderCompanyFactoryOptions();
    syncFactorySelection();
    setMessage("kcEditorMessage", `${state.companyFactories.length}件の会社工場を、工場名順で読み込みました。`);
  }

  async function registerFactoryCandidate() {
    const form = document.getElementById("kcCaptureForm");
    const factoryName = clean(form?.elements.factory.value);
    if (!factoryName) throw new Error("FACTORY_NAME_REQUIRED");
    const bridge = window.KC_PHOTO_CAPTURE_FACTORY_BRIDGE;
    if (!bridge) throw new Error("FACTORY_BRIDGE_UNAVAILABLE");
    const result = await bridge.createCandidate(factoryName);
    await loadCompanyFactories();
    setMessage("kcEditorMessage", `${result.factory_name || factoryName}を会社の要確認工場候補へ追加しました。`);
  }

  async function openEditor(recordId = "") {
    const form = document.getElementById("kcCaptureForm");
    form.reset();
    state.pendingFiles.clear();
    state.removedPhotoIds.clear();
    state.processingPhotos.clear();
    state.editingRecordId = recordId;
    const event = state.latestRecords.find((item) => item.recordId === recordId);
    const row = event?.snapshot || {};
    state.existingPhotoRefs = Array.isArray(row.photoRefs) ? [...row.photoRefs] : [];
    form.elements.record_id.value = recordId;
    form.elements.priority.value = row.priority || "NORMAL";
    form.elements.entry_date.value = row.entryDate || todayJst();
    form.elements.attention_rating.value = event ? attentionRatingForEditor(row.attentionRating, row.priority) : "★（参考）";
    form.elements.document_type.value = documentTypeForEditor(row.documentType);
    form.elements.visit_context.value = row.visitContext || "";
    form.elements.supplier.value = row.supplier || "";
    refreshSupplierOptionsForVisitContext();
    form.elements.yarn_name.value = row.yarnName || "";
    form.elements.factory.value = row.factory || "";
    form.elements.factory_id.value = row.factoryId || "";
    form.elements.factory_relationship_id.value = row.factoryRelationshipId || "";
    form.elements.factory_review_status.value = row.factoryReviewStatus || (row.factory ? "REVIEW_REQUIRED" : "");
    form.elements.factory_name_snapshot.value = row.factoryNameSnapshot || row.factory || "";
    form.elements.abbreviation.value = row.abbreviation || "";
    form.elements.yarn_structure.value = YARN_STRUCTURES.includes(row.yarnStructure) ? row.yarnStructure : (row.yarnStructure ? "その他" : "未確認");
    form.elements.yarn_structure_other.value = row.yarnStructureOther
      || (!YARN_STRUCTURES.includes(row.yarnStructure) && row.yarnStructure ? row.yarnStructure : "");
    form.elements.yarn_count.value = row.yarnCount || "";
    form.elements.composition.value = row.composition || "";
    form.elements.price.value = row.price || "";
    setSelectValuePreserving(form.elements.currency, row.currency || "CNY");
    form.elements.price_unit.value = row.priceUnit || "kg";
    const normalizedGauge = gaugeRange(row.gaugeMin, row.gaugeMax, row.gauge);
    setSelectValuePreserving(form.elements.gauge, normalizedGauge.label);
    form.elements.knitting_end_count.value = normalizeKnittingEndCount(row.knittingEndCount);
    setSelectValuePreserving(form.elements.knit_structure, row.knitStructure || "");
    const tactile = tactileFeelingsForEditor(row.tactileFeelings);
    setChecked(form.elements.tactile_feelings, tactile.selected);
    form.elements.legacy_tactile_feelings.value = JSON.stringify(tactile.legacy);
    document.getElementById("kcLegacyFeelingStatus").textContent = tactile.legacy.length
      ? `旧入力値「${tactile.legacy.join(" / ")}」もデータ上は保持します。`
      : "";
    form.elements.functional_fiber_usage.value = row.functionalFiberUsage || "未確認";
    form.elements.functional_fiber_detail.value = row.functionalFiberDetail || "";
    form.elements.sustainable_fiber_usage.value = row.sustainableFiberUsage || "未確認";
    form.elements.sustainable_fiber_detail.value = row.sustainableFiberDetail || "";
    form.elements.actual_count_structure.value = row.actualCountStructure || "";
    const spinning = spinningMethodChoiceForEditor(row.spinningMethod);
    form.elements.spinning_method.value = row.spinningMethodOther ? (spinning.value || "その他") : spinning.value;
    form.elements.spinning_method_other.value = row.spinningMethodOther || spinning.other;
    const filament = filamentTypeChoiceForEditor(row.filamentTypeObservation);
    form.elements.filament_type_observation.value = filament.value;
    form.elements.filament_type_other.value = row.filamentTypeOther || filament.other;
    const composite = companyChoiceForEditor(row.compositeStructureObservation || row.coveringStructure, COMPOSITE_STRUCTURES);
    form.elements.composite_structure_observation.value = row.compositeStructureObservation ? composite.value : "";
    form.elements.composite_structure_other.value = row.compositeStructureOther || (row.compositeStructureObservation ? composite.other : "");
    setChecked(form.elements.knitting_techniques, row.knittingTechniques);
    form.elements.color_sample.value = row.colorSample || "";
    form.elements.book_availability.value = row.bookAvailability || "";
    setChecked(form.elements.sample_status, sampleStatusForEditor(row.sampleStatus, row.colorSample));
    setChecked(form.elements.development_actions, row.developmentActions);
    form.elements.processing_method.value = row.processingMethod || "";
    form.elements.covering_structure.value = row.coveringStructure || "";
    setSelected(form.elements.outer_filament, row.outerFilament);
    const editorSeasons = seasonsForEditor(row.seasons);
    form.elements.season.value = editorSeasons[0] || "";
    form.elements.book_request.value = row.bookRequest || "未確認";
    form.elements.fabric_request.value = row.fabricRequest || "未確認";
    form.elements.arrangement_memo.value = row.arrangementMemo || "";
    form.elements.research_request.value = row.researchRequest === "不必要" ? "不要" : (row.researchRequest || "不要");
    form.elements.data_state.value = "DRAFT";
    form.elements.human_review_status.value = event?.humanReviewStatus || "NOT_REVIEWED";
    form.elements.notes.value = row.notes || "";
    const knitCompassDetails = form.querySelector(".kc-kc-details");
    if (knitCompassDetails) knitCompassDetails.open = Boolean(
      row.documentType || row.yarnCount || row.composition || row.yarnStructure || row.knittingEndCount || row.functionalFiberUsage
      || (row.seasons || []).length || (row.currency && row.currency !== "CNY") || row.abbreviation
      || row.actualCountStructure || row.processingMethod || row.coveringStructure || (row.outerFilament || []).length
      || row.factory || row.bookRequest || row.fabricRequest || row.arrangementMemo || row.researchRequest
    );
    syncFactorySelection({ preserveStored: true });
    syncCompatibilityDetailVisibility();
    document.getElementById("kcEditorTitle").textContent = event ? "DRAFTを編集" : "新規キャプチャ";
    setMessage("kcEditorMessage", event ? `Version ${event.version}の最新値を復元しました。保存するとUPDATEイベントを追加します。` : "写真または糸情報を入力してDRAFT保存してください。");
    document.getElementById("kcEditor").hidden = false;
    updateSaveButtonState();
    await renderEditorPhotoPreviews();
    document.getElementById("kcEditor").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function closeEditor() {
    state.editingRecordId = "";
    state.existingPhotoRefs = [];
    state.pendingFiles.clear();
    state.removedPhotoIds.clear();
    state.processingPhotos.clear();
    document.getElementById("kcEditor").hidden = true;
    document.getElementById("kcInbox").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  async function previewSelectedFile(input) {
    const type = input.dataset.photoInput;
    const files = [...(input.files || [])];
    if (!files.length) return;
    const remaining = MAX_PHOTOS_PER_RECORD - activePhotoCount();
    if (remaining <= 0) {
      setMessage("kcEditorMessage", `写真は合計${MAX_PHOTOS_PER_RECORD}枚までです。不要な写真を外してから追加してください。`, true);
      input.value = "";
      return;
    }
    const selected = files.slice(0, remaining);
    const processingId = createId(`KCI-PROCESS-${type.toUpperCase()}`);
    setPhotoProcessing(processingId, true);
    setMessage("kcEditorMessage", `${photoTypeDefinition(type).label}の画像を補正中です...`);
    try {
      for (const file of selected) {
        const entry = await processImageFile(file, { sourceMode: input.dataset.photoSource || "unknown" });
        entry.clientPhotoId = createId("KCI-PENDING-PHOTO");
        entry.type = type;
        entry.replacesPhotoId = "";
        state.pendingFiles.set(entry.clientPhotoId, entry);
      }
      await renderEditorPhotoPreviews();
      const omitted = files.length - selected.length;
      setMessage("kcEditorMessage", `${photoTypeDefinition(type).label}に${selected.length}枚追加しました。${omitted > 0 ? `上限10枚のため${omitted}枚は追加していません。` : "向きを確認してDRAFT保存してください。"}`);
    } catch (error) {
      setMessage("kcEditorMessage", `写真を読み込めませんでした: ${error.message || error}。JPEGまたはPNGで再度お試しください。`, true);
    } finally {
      await renderEditorPhotoPreviews();
      setPhotoProcessing(processingId, false);
      input.value = "";
    }
  }

  async function rotatePendingPhoto(entryId, delta) {
    const entry = state.pendingFiles.get(entryId);
    if (!entry) return;
    setPhotoProcessing(entryId, true);
    try {
      const rotated = await processImageFile(entry.originalFile, {
        sourceMode: entry.sourceMode,
        manualRotationDegree: normalizeRotation(entry.manualRotationDegree + Number(delta)),
        fileName: entry.file.name
      });
      Object.assign(rotated, { clientPhotoId: entry.clientPhotoId, type: entry.type, replacesPhotoId: entry.replacesPhotoId || "" });
      state.pendingFiles.set(entryId, rotated);
      await renderEditorPhotoPreviews();
    } catch (error) {
      setMessage("kcEditorMessage", `回転できませんでした: ${error.message || error}`, true);
    } finally {
      setPhotoProcessing(entryId, false);
    }
  }

  async function existingPhotoAsPending(photoId, rotationDegree = 0) {
    const existing = state.existingPhotoRefs.find((ref) => ref.photoId === photoId);
    if (!existing) throw new Error("EXISTING_PHOTO_NOT_FOUND");
    const loaded = await loadPhoto(existing.photoId);
    if (!loaded?.record?.blob) throw new Error("EXISTING_PHOTO_BLOB_NOT_FOUND");
    const originalFile = new File([loaded.record.blob], loaded.record.fileName || captureFileName("jpg"), {
      type: loaded.record.mediaType || loaded.record.blob.type || "image/jpeg",
      lastModified: Date.now()
    });
    return processImageFile(originalFile, { sourceMode: "existing", manualRotationDegree: rotationDegree });
  }

  async function rotateExistingPhoto(photoId, delta) {
    setPhotoProcessing(photoId, true);
    try {
      const existing = state.existingPhotoRefs.find((ref) => ref.photoId === photoId);
      if (!existing) throw new Error("EXISTING_PHOTO_NOT_FOUND");
      const entry = await existingPhotoAsPending(photoId, Number(delta));
      entry.clientPhotoId = `replace-${photoId}`;
      entry.type = existing.type;
      entry.replacesPhotoId = photoId;
      state.pendingFiles.set(entry.clientPhotoId, entry);
      await renderEditorPhotoPreviews();
      setMessage("kcEditorMessage", "保存済み写真を補正しました。DRAFT保存すると、新しい写真IDでUPDATEが追加されます。");
    } catch (error) {
      setMessage("kcEditorMessage", `保存済み写真を補正できませんでした: ${error.message || error}`, true);
      await renderEditorPhotoPreviews();
    } finally {
      setPhotoProcessing(photoId, false);
    }
  }

  async function downloadExistingPhoto(photoId) {
    setPhotoProcessing(photoId, true);
    try {
      const entry = await existingPhotoAsPending(photoId, 0);
      triggerFileDownload(entry.file);
      setMessage("kcEditorMessage", "補正済み写真を端末のDownloadフォルダへ保存しました。端末により保存確認が表示される場合があります。");
    } catch (error) {
      setMessage("kcEditorMessage", `端末保存できませんでした: ${error.message || error}`, true);
    } finally {
      setPhotoProcessing(photoId, false);
    }
  }

  function clearPendingPhoto(entryId) {
    state.pendingFiles.delete(entryId);
    renderEditorPhotoPreviews();
  }

  function removeExistingPhoto(photoId) {
    state.removedPhotoIds.add(photoId);
    state.pendingFiles.delete(`replace-${photoId}`);
    renderEditorPhotoPreviews();
    setMessage("kcEditorMessage", "写真を外しました。DRAFT保存後も過去のイベント履歴には残ります。");
  }

  function preparePhotos(form, recordId) {
    const prepared = [];
    sortPhotoEntries([...state.pendingFiles.values()]).forEach((entry) => {
      if (!entry?.file) return;
      const file = entry.file;
      const type = photoTypeDefinition(entry.type);
      const photoId = createId(`KCI-PHOTO-${type.key.toUpperCase()}`);
      const capturedAt = isoNow();
      const orientationMetadata = {
        captureSource: entry.sourceMode,
        captureOrientationOriginal: entry.orientationOriginal,
        captureOrientationFinal: entry.orientationFinal,
        orientationNormalized: true,
        manualRotationDegree: entry.manualRotationDegree,
        originalExifOrientation: entry.exifOrientation,
        pixelWidth: entry.width,
        pixelHeight: entry.height,
        originalPixelWidth: entry.originalWidth,
        originalPixelHeight: entry.originalHeight,
        normalizedAt: entry.normalizedAt
      };
      prepared.push({
        ref: { photoId, type: entry.type, label: type.label, fileName: file.name, capturedAt, replacesPhotoId: entry.replacesPhotoId || "", ...orientationMetadata },
        record: {
          photoId, recordId, type: entry.type, label: type.label, fileName: file.name,
          originalFileName: entry.originalFile?.name || "", mediaType: file.type || "image/jpeg", size: file.size,
          originalSize: entry.originalFile?.size || null, blob: file, capturedAt,
          actorId: state.session.accountId, storageRealm: CONTRACT.photo_store, ...orientationMetadata
        }
      });
    });
    return prepared;
  }

  function collectSnapshot(form, photoRefs) {
    const values = new FormData(form);
    const existingSnapshot = state.latestRecords.find((item) => item.recordId === state.editingRecordId)?.snapshot || {};
    const attentionRating = clean(values.get("attention_rating"));
    const tactileFeelings = [...form.elements.tactile_feelings].filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value);
    const legacyTactileFeelings = parseStringArray(values.get("legacy_tactile_feelings"));
    const normalizedGauge = gaugeRange("", "", values.get("gauge"));
    const visitContext = clean(values.get("visit_context"));
    const supplier = clean(values.get("supplier"));
    const sourceEvent = exhibitionForVisitContext(visitContext);
    const supplierMaster = supplierRecordForEvent(sourceEvent, supplier);
    const sampleStatus = [...form.elements.sample_status].filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value);
    const legacyColorSample = clean(existingSnapshot.colorSample || values.get("color_sample"));
    return {
      ...existingSnapshot,
      companyFormAlignmentVersion: "COMPANY_MATERIAL_PHOTO_CURRENT",
      companySpreadsheetPayloadSchema: CONTRACT.company_spreadsheet_payload_schema,
      priority: priorityFromAttentionRating(attentionRating),
      attentionRating,
      entryDate: clean(values.get("entry_date")) || todayJst(),
      operatorName: clean(existingSnapshot.operatorName),
      department: clean(existingSnapshot.department),
      documentType: clean(values.get("document_type")),
      visitContext,
      sourceEventId: sourceEvent?.id || "",
      supplier,
      supplierMasterId: supplierMaster?.supplier_master_id || supplierMaster?.id || "",
      yarnName: clean(values.get("yarn_name")),
      factory: clean(values.get("factory")),
      factoryId: clean(values.get("factory_id")),
      factoryRelationshipId: clean(values.get("factory_relationship_id")),
      factoryReviewStatus: clean(values.get("factory_review_status")) || (clean(values.get("factory")) ? "REVIEW_REQUIRED" : ""),
      factoryNameSnapshot: clean(values.get("factory_name_snapshot")) || clean(values.get("factory")),
      abbreviation: clean(values.get("abbreviation")),
      yarnCount: clean(values.get("yarn_count")),
      qualityLabel: existingSnapshot.qualityLabel || "",
      specificationText: existingSnapshot.specificationText || "",
      yarnStructure: clean(values.get("yarn_structure")) || "未確認",
      yarnStructureOther: clean(values.get("yarn_structure_other")),
      composition: clean(values.get("composition")),
      price: clean(values.get("price")),
      currency: clean(values.get("currency")) || "CNY",
      priceUnit: clean(values.get("price_unit")) || "kg",
      gauge: normalizedGauge.label,
      gaugeMin: normalizedGauge.min,
      gaugeMax: normalizedGauge.max,
      knittingEndCount: normalizeKnittingEndCount(values.get("knitting_end_count")),
      knitStructure: clean(values.get("knit_structure")),
      knittingTechniques: [...form.elements.knitting_techniques].filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value),
      colorSample: sampleStatus.includes(BOOK_SAMPLE_STATUS) ? "あり" : (legacyColorSample === "なし" ? "なし" : "未確認"),
      bookAvailability: clean(values.get("book_availability")),
      sampleStatus,
      tactileFeelings: [...new Set([...tactileFeelings, ...legacyTactileFeelings])],
      functionalFiberUsage: clean(values.get("functional_fiber_usage")) || "未確認",
      functionalFiberDetail: clean(values.get("functional_fiber_usage")) === "あり" ? clean(values.get("functional_fiber_detail")) : "",
      sustainableFiberUsage: clean(values.get("sustainable_fiber_usage")) || "未確認",
      sustainableFiberDetail: clean(values.get("sustainable_fiber_usage")) === "あり" ? clean(values.get("sustainable_fiber_detail")) : "",
      actualCountStructure: clean(values.get("actual_count_structure")),
      spinningMethod: canonicalSpinningMethod(values.get("spinning_method")),
      spinningMethodOther: clean(values.get("spinning_method_other")),
      filamentTypeObservation: canonicalFilamentType(values.get("filament_type_observation")),
      filamentTypeOther: clean(values.get("filament_type_other")),
      compositeStructureObservation: clean(values.get("composite_structure_observation")),
      compositeStructureOther: clean(values.get("composite_structure_other")),
      developmentActions: [...form.elements.development_actions].filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value),
      processingMethod: clean(values.get("processing_method")),
      coveringStructure: clean(values.get("covering_structure")),
      outerFilament: selectedValues(form.elements.outer_filament),
      seasons: [clean(values.get("season"))].filter(Boolean),
      bookRequest: clean(values.get("book_request")),
      fabricRequest: clean(values.get("fabric_request")),
      arrangementMemo: clean(values.get("arrangement_memo")),
      researchRequest: clean(values.get("research_request")),
      notes: clean(values.get("notes")),
      photoRefs
    };
  }

  function hasDraftContent(snapshot) {
    const yarnStructure = ["", "未確認", "不明"].includes(clean(snapshot.yarnStructure)) ? "" : snapshot.yarnStructure;
    const functionalFiberUsage = ["", "未確認"].includes(clean(snapshot.functionalFiberUsage)) ? "" : snapshot.functionalFiberUsage;
    const sustainableFiberUsage = ["", "未確認"].includes(clean(snapshot.sustainableFiberUsage)) ? "" : snapshot.sustainableFiberUsage;
    const researchRequest = clean(snapshot.researchRequest) === "必要" ? snapshot.researchRequest : "";
    const attentionRating = clean(snapshot.attentionRating) === "★（参考）" ? "" : snapshot.attentionRating;
    return snapshot.photoRefs.length > 0 || [
      snapshot.documentType, snapshot.visitContext, snapshot.supplier, snapshot.yarnName, snapshot.factory, snapshot.abbreviation,
      snapshot.yarnCount, snapshot.qualityLabel, snapshot.specificationText, yarnStructure, snapshot.yarnStructureOther, snapshot.composition,
      snapshot.price, snapshot.gauge, snapshot.knittingEndCount, snapshot.knitStructure,
      functionalFiberUsage, snapshot.functionalFiberDetail, sustainableFiberUsage, snapshot.sustainableFiberDetail,
      snapshot.actualCountStructure, snapshot.processingMethod, snapshot.arrangementMemo,
      researchRequest, snapshot.notes, attentionRating, snapshot.spinningMethod, snapshot.spinningMethodOther,
      snapshot.filamentTypeObservation, snapshot.filamentTypeOther, snapshot.compositeStructureObservation,
      snapshot.compositeStructureOther, snapshot.colorSample, snapshot.bookAvailability
    ].some(Boolean) || snapshot.tactileFeelings.length > 0 || snapshot.seasons.length > 0
      || snapshot.knittingTechniques.length > 0 || snapshot.sampleStatus.length > 0 || snapshot.developmentActions.length > 0;
  }

  function missingCompanyRequiredFields(snapshot) {
    return [
      [snapshot.entryDate, "登録日"],
      [snapshot.photoRefs.length > 0, "写真"],
      [snapshot.attentionRating, "重要度"]
    ].filter(([value]) => !value).map(([, label]) => label);
  }

  async function saveDraft(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const saveDestination = event.submitter?.dataset.saveDestination === "LOCAL" ? "LOCAL" : "INBOX";
    if (state.processingPhotos.size > 0) {
      setMessage("kcEditorMessage", "写真の補正処理が完了するまでお待ちください。", true);
      return;
    }
    state.isSaving = true;
    state.saveDestination = saveDestination;
    updateSaveButtonState();
    try {
      const latest = state.latestRecords.find((item) => item.recordId === state.editingRecordId);
      const recordId = latest?.recordId || createId("KCI-CAPTURE");
      const preparedPhotos = preparePhotos(form, recordId);
      const replacementPhotoIds = new Set(preparedPhotos.map((item) => item.ref.replacesPhotoId).filter(Boolean));
      const retainedRefs = state.existingPhotoRefs.filter((ref) => !state.removedPhotoIds.has(ref.photoId) && !replacementPhotoIds.has(ref.photoId));
      const photoRefs = sortPhotoEntries([...retainedRefs, ...preparedPhotos.map((item) => item.ref)]);
      if (photoRefs.length > MAX_PHOTOS_PER_RECORD) throw new Error(`PHOTO_LIMIT_EXCEEDED_${MAX_PHOTOS_PER_RECORD}`);
      const snapshot = collectSnapshot(form, photoRefs);
      if (!hasDraftContent(snapshot)) throw new Error("DRAFT_CONTENT_REQUIRED");
      const missingRequired = missingCompanyRequiredFields(snapshot);
      if (saveDestination === "INBOX" && missingRequired.length) {
        setMessage("kcEditorMessage", `外部取込ZIPを書き出す前に入力してください：${missingRequired.join("、")}。途中の場合は「端末にDRAFT保存」を選べます。`, true);
        return;
      }
      const now = isoNow();
      const eventType = latest ? "UPDATE" : "CREATE";
      const version = latest ? latest.version + 1 : 1;
      const snapshotSha256 = await snapshotHash(snapshot);
      const eventRecord = {
        eventId: createId("KCI-EVENT"),
        recordId,
        version,
        eventType,
        dataState: "DRAFT",
        humanReviewStatus: clean(form.elements.human_review_status.value) || "NOT_REVIEWED",
        originalPhotoIds: photoRefs.map((ref) => ref.photoId),
        actorId: state.session.accountId,
        actorDisplayName: state.session.displayName,
        createdAt: latest?.createdAt || now,
        updatedAt: now,
        snapshot,
        historyPolicy: "APPEND_ONLY",
        automaticSync: "OFF",
        automaticPublish: "OFF"
      };
      const auditRecord = {
        auditId: createId("KCI-AUDIT"),
        eventId: eventRecord.eventId,
        recordId,
        version,
        eventType,
        dataState: "DRAFT",
        humanReviewStatus: eventRecord.humanReviewStatus,
        originalPhotoIds: eventRecord.originalPhotoIds,
        actorId: state.session.accountId,
        registeredAt: eventRecord.createdAt,
        updatedAt: now,
        createdAt: now,
        snapshotSha256,
        auditRealm: CONTRACT.audit_store
      };
      const tx = state.db.transaction([STORES.events, STORES.audit, STORES.photos], "readwrite");
      tx.objectStore(STORES.events).add(eventRecord);
      tx.objectStore(STORES.audit).add(auditRecord);
      preparedPhotos.forEach((item) => tx.objectStore(STORES.photos).add(item.record));
      await transactionPromise(tx);
      await loadEvents();
      refreshCandidateOptions();
      renderRecords();
      closeEditor();
      if (saveDestination === "INBOX") {
        setMessage("kcInboxMessage", "端末へのDRAFT保存が完了しました。外部取込ZIPを作成しています。");
        try {
          await exportPortablePackage(recordId);
          setMessage("kcInboxMessage", "DRAFT保存と外部取込ZIPの書き出しが完了しました。取込先でHuman Reviewを行ってください。");
        } catch (exportError) {
          setMessage("kcInboxMessage", `DRAFTは端末に保存しましたが、ZIPを書き出せませんでした。一覧の「外部取込ZIPを書き出す」から再実行できます: ${exportError.message || exportError}`, true);
        }
      } else {
        setMessage("kcInboxMessage", `${eventType}イベントを端末へAppend Onlyで保存しました。状態はDRAFTです。外部へは送信されていません。`);
      }
    } catch (error) {
      setMessage("kcEditorMessage", `保存できませんでした: ${error.message || error}`, true);
    } finally {
      state.isSaving = false;
      state.saveDestination = "LOCAL";
      updateSaveButtonState();
    }
  }

  function clearSearch() {
    state.filters = { query: "", supplier: "", yarnName: "", abbreviation: "", season: "" };
    ["kcSearchAll", "kcSearchSupplier", "kcSearchYarnName", "kcSearchAbbreviation", "kcSearchSeason"].forEach((id) => {
      const control = document.getElementById(id);
      if (control) control.value = "";
    });
    renderRecords();
  }

  function wireApplication() {
    document.getElementById("kcNewCapture").addEventListener("click", () => openEditor());
    document.getElementById("kcLogout").addEventListener("click", () => {
      sessionStorage.removeItem(SESSION_KEY);
      state.session = null;
      void renderDeviceAuth();
    });
    document.getElementById("kcCancelEdit").addEventListener("click", closeEditor);
    const captureForm = document.getElementById("kcCaptureForm");
    captureForm.addEventListener("submit", saveDraft);
    captureForm.elements.factory.addEventListener("input", () => syncFactorySelection());
    captureForm.elements.visit_context.addEventListener("input", refreshSupplierOptionsForVisitContext);
    captureForm.elements.visit_context.addEventListener("change", refreshSupplierOptionsForVisitContext);
    ["functional_fiber_usage", "sustainable_fiber_usage", "yarn_structure"].forEach((fieldName) => {
      captureForm.elements[fieldName].addEventListener("change", syncCompatibilityDetailVisibility);
    });
    captureForm.addEventListener("change", (event) => {
      if (event.target.matches("[data-photo-input]")) void previewSelectedFile(event.target);
    });
    captureForm.addEventListener("click", (event) => {
      const rotate = event.target.closest("[data-photo-rotate]");
      if (rotate) return void rotatePendingPhoto(rotate.dataset.photoEntry, Number(rotate.dataset.photoRotate));
      const rotateExisting = event.target.closest("[data-photo-rotate-existing]");
      if (rotateExisting) return void rotateExistingPhoto(rotateExisting.dataset.photoId, Number(rotateExisting.dataset.photoRotateExisting));
      const download = event.target.closest("[data-photo-download]");
      if (download) {
        const entry = state.pendingFiles.get(download.dataset.photoDownload);
        if (entry?.file) {
          triggerFileDownload(entry.file);
          setMessage("kcEditorMessage", "補正済み写真を端末のDownloadフォルダへ保存しました。端末により保存確認が表示される場合があります。");
        }
        return;
      }
      const downloadExisting = event.target.closest("[data-photo-download-existing]");
      if (downloadExisting) return void downloadExistingPhoto(downloadExisting.dataset.photoDownloadExisting);
      const remove = event.target.closest("[data-photo-remove]");
      if (remove) return clearPendingPhoto(remove.dataset.photoRemove);
      const removeExisting = event.target.closest("[data-photo-remove-existing]");
      if (removeExisting) return removeExistingPhoto(removeExisting.dataset.photoRemoveExisting);
    });
    [
      ["kcSearchAll", "query", "input"],
      ["kcSearchSupplier", "supplier", "input"],
      ["kcSearchYarnName", "yarnName", "input"],
      ["kcSearchAbbreviation", "abbreviation", "input"],
      ["kcSearchSeason", "season", "change"]
    ].forEach(([id, key, eventName]) => {
      document.getElementById(id).addEventListener(eventName, (event) => {
        state.filters[key] = clean(event.target.value);
        renderRecords();
      });
    });
    document.getElementById("kcClearSearch").addEventListener("click", clearSearch);
    document.getElementById("kcPortableImport").addEventListener("change", (event) => {
      void importPortableFiles(event.target.files);
    });
    window.addEventListener("online", () => {
      state.isOnline = true;
      renderRecords();
      updateConnectivityStatus(true);
    });
    window.addEventListener("offline", () => {
      state.isOnline = false;
      renderRecords();
      updateConnectivityStatus(true);
    });
    document.getElementById("kcRecordList").addEventListener("click", (event) => {
      const createButton = event.target.closest("[data-empty-create]");
      if (createButton) return openEditor();
      const clearButton = event.target.closest("[data-empty-clear]");
      if (clearButton) return clearSearch();
      const editButton = event.target.closest("[data-edit]");
      if (editButton) return openEditor(editButton.dataset.edit);
      const exportButton = event.target.closest("[data-portable-export]");
      if (exportButton) {
        void exportPortablePackage(exportButton.dataset.portableExport).catch((error) => {
          setMessage("kcInboxMessage", `外部取込ZIPを作成できませんでした: ${error.message || error}`, true);
        });
        return;
      }
      const detailButton = event.target.closest("[data-detail]");
      if (detailButton) {
        const panel = document.querySelector(`[data-detail-panel="${CSS.escape(detailButton.dataset.detail)}"]`);
        const expanding = panel.hidden;
        panel.hidden = !expanding;
        detailButton.setAttribute("aria-expanded", String(expanding));
        detailButton.textContent = expanding ? "保存内容を閉じる" : "保存内容を表示";
      }
    });
  }

  async function renderApplication() {
    app.innerHTML = appTemplate();
    document.getElementById("kcSessionIdentity").textContent = state.session.displayName;
    const accounts = await getAll(STORES.accounts);
    document.getElementById("kcLogout").hidden = accounts.length <= 1;
    wireApplication();
    await loadEvents();
    refreshCandidateOptions();
    renderRecords();
    updateConnectivityStatus();
  }

  async function initialize() {
    try {
      state.db = await withStartupTimeout(openDatabase(), 8000, "端末内DRAFTの確認がタイムアウトしました");
      await withStartupTimeout(seedIndependentMasters(), 8000, "端末内DRAFTの初期化がタイムアウトしました");
      await withStartupTimeout(readMasters(), 8000, "端末内マスターの読込みがタイムアウトしました");
      state.session = loadDeviceSession() || await ensureImmediateDeviceSession();
      if (state.session) {
        await renderApplication();
      } else {
        await renderDeviceAuth();
      }
    } catch (error) {
      app.innerHTML = sessionErrorTemplate(error.message || error);
    }
  }

  function registerInstallableAppShell() {
    if (typeof navigator === "undefined" || !("serviceWorker" in navigator)) return;
    window.addEventListener("load", () => {
      const appBasePath = new URL(".", window.location.href).pathname;
      navigator.serviceWorker.register(`${appBasePath}service-worker.js?v=2.1.43-current-ui-direct-entry`, {
        scope: appBasePath,
        updateViaCache: "none"
      }).catch(() => {});
    }, { once: true });
  }

  window.addEventListener("beforeunload", revokeObjectUrls);
  window.KC_INDEPENDENT_PHOTO_CAPTURE_V1_1_CANDIDATE = Object.freeze({
    contract: CONTRACT,
    async getRuntimeSnapshot() {
      const [events, audits, photos] = await Promise.all([getAll(STORES.events), getAll(STORES.audit), getAll(STORES.photos)]);
      return {
        eventCount: events.length,
        auditCount: audits.length,
        photoCount: photos.length,
        eventTypes: events.map((event) => event.eventType),
        dataStates: events.map((event) => event.dataState),
        automaticSync: CONTRACT.automatic_sync,
        automaticPublish: CONTRACT.automatic_publish,
        databaseName: CONTRACT.database_name
      };
    }
  });

  initialize();
})();
