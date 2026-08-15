(() => {
  'use strict';

  if (window.KnitCompassMetrics) return;
  const STORAGE_KEY = 'kc_usage_metrics_v1';
  const FORMAT = 'KC_USAGE_METRICS';
  const MAX_DAYS = 120;
  const WORKFLOW_BY_PATH = [
    ['/owner-yarns/', 'yarn_search'],
    ['/market-intelligence/', 'raw_material_market'],
    ['/knit-image/', 'knit_image'],
    ['/fabric-inspection/', 'fabric_inspection'],
    ['/brand-intelligence/', 'product_research'],
    ['/customer-sharing/', 'customer_sharing'],
    ['/stylem/', 'customer_portal'],
    ['/daily/', 'daily'],
    ['/status/', 'system_admin']
  ];
  const workflow = WORKFLOW_BY_PATH.find(([path]) => location.pathname.includes(path))?.[1] || 'photo_capture';
  const localDate = () => {
    const value = new Date();
    value.setMinutes(value.getMinutes() - value.getTimezoneOffset());
    return value.toISOString().slice(0, 10);
  };
  const cleanToken = (value) => String(value || '').replace(/[^a-z0-9_-]/gi, '_').slice(0, 80) || 'unknown';

  function emptyState() {
    return { format: FORMAT, schema_version: '1.0', privacy: 'DAILY_AGGREGATES_NO_INPUT_CONTENT', days: {} };
  }

  function load() {
    try {
      const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      return parsed?.format === FORMAT && parsed.days && typeof parsed.days === 'object' ? parsed : emptyState();
    } catch {
      return emptyState();
    }
  }

  function save(state) {
    const days = Object.keys(state.days).sort().slice(-MAX_DAYS);
    state.days = Object.fromEntries(days.map((day) => [day, state.days[day]]));
    state.updated_at = new Date().toISOString();
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch { /* 利用画面を止めない */ }
  }

  function track(eventType, selectedWorkflow = workflow) {
    const state = load();
    const day = localDate();
    const key = `${cleanToken(selectedWorkflow)}.${cleanToken(eventType)}`;
    state.days[day] = state.days[day] || {};
    state.days[day][key] = Number(state.days[day][key] || 0) + 1;
    save(state);
    renderStatus();
  }

  function totals(state = load()) {
    const entries = Object.entries(state.days).sort(([a], [b]) => a.localeCompare(b));
    const totalEvents = entries.reduce((sum, [, metrics]) => sum + Object.values(metrics).reduce((part, count) => part + Number(count || 0), 0), 0);
    const searchCount = entries.reduce((sum, [, metrics]) => sum + Object.entries(metrics).filter(([key]) => key.endsWith('.search')).reduce((part, [, count]) => part + Number(count || 0), 0), 0);
    const submitCount = entries.reduce((sum, [, metrics]) => sum + Object.entries(metrics).filter(([key]) => key.endsWith('.form_submit')).reduce((part, [, count]) => part + Number(count || 0), 0), 0);
    return { activeDays: entries.length, totalEvents, searchCount, submitCount, lastDate: entries.at(-1)?.[0] || '記録なし' };
  }

  function csvCell(value) {
    let text = String(value ?? '');
    if (/^[=+\-@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  }

  function exportCsv() {
    const state = load();
    const headers = ['measurement_date','operator','workflow','event_type','item_type','item_id','registration_status','confirmed_at','baseline_minutes','actual_minutes','minutes_saved','ai_tool','ai_correction_count','human_review_status','evidence_id','evidence_status','reuse_count','active_user_count','notes'];
    const rows = [];
    Object.entries(state.days).sort(([a], [b]) => a.localeCompare(b)).forEach(([day, metrics]) => {
      Object.entries(metrics).sort(([a], [b]) => a.localeCompare(b)).forEach(([key, count]) => {
        const splitAt = key.indexOf('.');
        rows.push({
          measurement_date: day, operator: '', workflow: key.slice(0, splitAt), event_type: key.slice(splitAt + 1),
          item_type: 'usage_metric', item_id: '', registration_status: 'LOCAL_AGGREGATE', confirmed_at: '',
          baseline_minutes: '', actual_minutes: '', minutes_saved: '', ai_tool: '', ai_correction_count: '',
          human_review_status: '', evidence_id: '', evidence_status: 'DEVICE_AGGREGATE', reuse_count: count,
          active_user_count: 1, notes: '入力内容・氏名・検索語を保存しない日次集計'
        });
      });
    });
    const content = '\uFEFF' + [headers.join(','), ...rows.map((row) => headers.map((key) => csvCell(row[key])).join(','))].join('\r\n');
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `KC_usage_metrics_${localDate()}.csv`;
    link.rel = 'noopener';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  function renderStatus() {
    const target = document.getElementById('kcUsageSummary');
    if (!target) return;
    const value = totals();
    target.innerHTML = [
      ['記録日数', `${value.activeDays}日`], ['操作合計', `${value.totalEvents}件`],
      ['検索', `${value.searchCount}回`], ['登録操作', `${value.submitCount}回`], ['最終利用', value.lastDate]
    ].map(([label, count]) => `<div><span>${label}</span><strong>${count}</strong></div>`).join('');
    const button = document.getElementById('kcExportUsageMetrics');
    if (button) button.onclick = exportCsv;
  }

  const pageMarker = `kc_metric_page_${cleanToken(location.pathname)}`;
  try {
    if (!sessionStorage.getItem(pageMarker)) {
      sessionStorage.setItem(pageMarker, '1');
      track('page_open');
    }
  } catch {
    track('page_open');
  }

  const searchTimers = new WeakMap();
  document.addEventListener('input', (event) => {
    if (!(event.target instanceof HTMLInputElement) || event.target.type !== 'search') return;
    clearTimeout(searchTimers.get(event.target));
    searchTimers.set(event.target, setTimeout(() => track('search'), 700));
  }, true);
  document.addEventListener('submit', () => track('form_submit'), true);
  document.addEventListener('click', (event) => {
    const element = event.target.closest('button,a');
    if (!element) return;
    const action = element.dataset.kcMetric || ({
      new: 'capture_start', exportHandoff: 'handoff_export', kcExportBackup: 'backup_export',
      kcVerifyBackup: 'backup_verify', exportCompanyCsv: 'company_backup_export',
      generate: 'knit_image_generate', exportJson: 'audit_export'
    })[element.id];
    if (action) track(action);
  }, true);

  window.KnitCompassMetrics = Object.freeze({ track, totals, exportCsv });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', renderStatus, { once: true });
  else renderStatus();
})();
