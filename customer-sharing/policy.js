(() => {
  'use strict';

  const CUSTOMER_ID = 'STYLEM';
  const CUSTOMER_NAME = 'スタイレム（暫定）';
  const PORTAL_KEY = 'kc_customer_portal_STYLEM_v1';
  const REQUESTS_KEY = 'kc_customer_requests_v1';
  const PORTAL_SCHEMA = '1.1';
  const MAX_IMAGE_DATA_LENGTH = 1500000;
  const ALLOWED_IMAGE_DATA = /^data:image\/(?:png|jpeg|webp|gif);base64,[a-z0-9+/=]+$/i;

  function nowIso() {
    return new Date().toISOString();
  }

  function safeParse(raw, fallback) {
    try {
      const parsed = JSON.parse(raw || 'null');
      return parsed === null ? fallback : parsed;
    } catch {
      return fallback;
    }
  }

  function cleanText(value, maxLength = 1000) {
    return String(value ?? '').trim().slice(0, maxLength);
  }

  function cleanList(value, maxItems = 20) {
    const values = Array.isArray(value) ? value : [];
    return values.map((item) => cleanText(item, 120)).filter(Boolean).slice(0, maxItems);
  }

  function cleanHttpUrl(value) {
    const text = cleanText(value, 1000);
    if (!text) return '';
    try {
      const url = new URL(text);
      if (!['http:', 'https:'].includes(url.protocol)) return '';
      return url.href.slice(0, 1000);
    } catch {
      return '';
    }
  }

  function cleanImageData(value) {
    const text = String(value ?? '').trim();
    if (!text || text.length > MAX_IMAGE_DATA_LENGTH || !ALLOWED_IMAGE_DATA.test(text)) return '';
    return text;
  }

  function uniqueById(records) {
    const result = [];
    const seen = new Set();
    for (const record of records) {
      if (!record?.id || seen.has(record.id)) continue;
      seen.add(record.id);
      result.push(record);
    }
    return result;
  }

  function isEligible(entityType, record) {
    if (!record || typeof record !== 'object') return false;
    if (entityType === 'product') return record.sourceStatus === 'CONFIRMED';
    if (entityType === 'yarn') return record.status === 'PUBLISHED';
    return false;
  }

  function normalizeSharedProduct(record) {
    if (!record || typeof record !== 'object') return null;
    const product = {
      entityType: 'product',
      id: cleanText(record.id, 120),
      brand: cleanText(record.brand, 160),
      name: cleanText(record.name, 240),
      productNumber: cleanText(record.productNumber, 160),
      category: cleanText(record.category, 160),
      composition: cleanText(record.composition, 500),
      colors: cleanList(record.colors),
      sizes: cleanList(record.sizes),
      officialUrl: cleanHttpUrl(record.officialUrl),
      productImageData: cleanImageData(record.productImageData),
      releaseStatus: cleanText(record.releaseStatus, 40),
      updatedAt: cleanText(record.updated_at || record.updatedAt, 80)
    };
    return product.id ? product : null;
  }

  function safeProduct(record) {
    if (!isEligible('product', record)) return null;
    return normalizeSharedProduct(record);
  }

  function normalizeSharedYarn(record) {
    if (!record || typeof record !== 'object') return null;
    const yarn = {
      entityType: 'yarn',
      id: cleanText(record.id, 120),
      supplier: cleanText(record.supplier, 240),
      name: cleanText(record.name, 240),
      code: cleanText(record.code, 160),
      displayCount: cleanText(record.displayCount, 160),
      structure: cleanText(record.structure, 160),
      composition: cleanText(record.composition, 500),
      gauge: cleanText(record.gauge, 160),
      functions: cleanList(record.functions),
      sourceUrl: cleanHttpUrl(record.sourceUrl),
      updatedAt: cleanText(record.updated_at || record.updatedAt, 80)
    };
    return yarn.id ? yarn : null;
  }

  function safeYarn(record) {
    if (!isEligible('yarn', record)) return null;
    return normalizeSharedYarn(record);
  }

  function emptyPortal() {
    return {
      schema_version: PORTAL_SCHEMA,
      customer_id: CUSTOMER_ID,
      customer_name: CUSTOMER_NAME,
      published_at: '',
      products: [],
      yarns: []
    };
  }

  function normalizePortal(value) {
    const source = value && typeof value === 'object' ? value : {};
    const products = Array.isArray(source.products)
      ? source.products.map(normalizeSharedProduct).filter(Boolean)
      : [];
    const yarns = Array.isArray(source.yarns)
      ? source.yarns.map(normalizeSharedYarn).filter(Boolean)
      : [];
    return {
      ...emptyPortal(),
      published_at: cleanText(source.published_at, 80),
      products: uniqueById(products),
      yarns: uniqueById(yarns)
    };
  }

  function normalizeRequests(value) {
    return (Array.isArray(value) ? value : []).map((request) => ({
      request_id: cleanText(request.request_id, 120),
      customer_id: cleanText(request.customer_id, 40),
      request_type: cleanText(request.request_type, 80),
      subject: cleanText(request.subject, 240),
      details: cleanText(request.details, 2000),
      status: ['OPEN', 'ANSWERED', 'CLOSED'].includes(request.status) ? request.status : 'OPEN',
      created_at: cleanText(request.created_at, 80),
      updated_at: cleanText(request.updated_at, 80),
      response: cleanText(request.response, 2000)
    })).filter((request) => request.customer_id === CUSTOMER_ID && request.request_id && request.subject);
  }

  function newRequest({ requestType, subject, details }) {
    const cleanSubject = cleanText(subject, 240);
    if (!cleanSubject) throw new Error('件名を入力してください。');
    const requestUuid = globalThis.crypto?.randomUUID?.()
      || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
    const timestamp = nowIso();
    return {
      request_id: `STYLEM-REQ-${requestUuid}`,
      customer_id: CUSTOMER_ID,
      request_type: cleanText(requestType, 80) || 'OTHER',
      subject: cleanSubject,
      details: cleanText(details, 2000),
      status: 'OPEN',
      created_at: timestamp,
      updated_at: timestamp,
      response: ''
    };
  }

  window.KCCustomerPolicy = Object.freeze({
    CUSTOMER_ID,
    CUSTOMER_NAME,
    PORTAL_KEY,
    REQUESTS_KEY,
    PORTAL_SCHEMA,
    nowIso,
    safeParse,
    cleanHttpUrl,
    cleanImageData,
    isEligible,
    normalizeSharedProduct,
    normalizeSharedYarn,
    safeProduct,
    safeYarn,
    emptyPortal,
    normalizePortal,
    normalizeRequests,
    newRequest
  });
})();
