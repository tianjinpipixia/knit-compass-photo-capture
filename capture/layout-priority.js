(() => {
  'use strict';

  const root = document.getElementById('app');
  if (!root) return;

  let moving = false;
  let queued = false;
  let primaryActions = null;
  let searchNode = null;
  let searchDrawer = null;
  let latestSummary = null;
  let latestSignature = '';

  function text(node) {
    return String(node?.textContent || '').trim();
  }

  function activeSearchFilters() {
    return [
      'kcSearchAll',
      'kcSearchSupplier',
      'kcSearchYarnName',
      'kcSearchAbbreviation',
      'kcSearchSeason'
    ].some((id) => String(document.getElementById(id)?.value || '').trim());
  }

  function isDefaultListingStatus(value) {
    const matched = String(value || '').trim().match(/^保存済み(\d+)件\s*\/\s*検索結果(\d+)件。最新値を表示しています。$/);
    return Boolean(matched && matched[1] === matched[2]);
  }

  function updateInboxMessageVisibility(inbox) {
    const message = inbox.querySelector('#kcInboxMessage');
    if (!message) return;
    const hideDefaultStatus = !activeSearchFilters() && isDefaultListingStatus(text(message));
    message.hidden = hideDefaultStatus;
  }

  function currentPrimaryActions(inbox) {
    const live = inbox.querySelector('.kc-panel-heading .kc-primary-actions')
      || inbox.querySelector('.kc-primary-actions');
    if (live && live !== primaryActions) primaryActions = live;
    return primaryActions;
  }

  function currentSearchNode(inbox) {
    const live = inbox.querySelector('.kc-search');
    if (live && live !== searchNode) {
      searchNode = live;
      searchDrawer = null;
    }
    return searchNode;
  }

  function ensureSearchDrawer(inbox) {
    const search = currentSearchNode(inbox);
    if (!search) return null;

    if (!searchDrawer || !searchDrawer.contains(search)) {
      const drawer = document.createElement('details');
      drawer.className = 'kc-mobile-search-drawer';
      drawer.innerHTML = `
        <summary>
          <span>保存済みデータを検索</span>
          <small data-kc-search-count></small>
        </summary>`;
      drawer.appendChild(search);
      searchDrawer = drawer;
    }

    if (activeSearchFilters()) searchDrawer.open = true;
    const count = searchDrawer.querySelector('[data-kc-search-count]');
    const message = text(inbox.querySelector('#kcInboxMessage'));
    const nextCount = message ? message.split('。')[0] : '';
    if (count && text(count) !== nextCount) count.textContent = nextCount;
    return searchDrawer;
  }

  function ensureLatestSummary(inbox) {
    if (!latestSummary || latestSummary.closest('#kcInbox') !== inbox) {
      latestSummary = document.createElement('section');
      latestSummary.id = 'kcLatestCaptureSummary';
      latestSummary.className = 'kc-mobile-latest-summary';
      latestSummary.setAttribute('aria-label', '直前に保存したデータ');
      latestSummary.innerHTML = `
        <div class="kc-mobile-latest-topline">
          <span>直前に保存したデータ</span>
          <small data-kc-latest-time></small>
        </div>
        <strong class="kc-mobile-latest-name" data-kc-latest-name></strong>
        <p class="kc-mobile-latest-supplier" data-kc-latest-supplier></p>
        <div class="kc-mobile-latest-specs" data-kc-latest-specs></div>`;
      latestSignature = '';
    }
    return latestSummary;
  }

  function updateLatestSummary(inbox, recordList) {
    const summary = ensureLatestSummary(inbox);
    const firstRecord = recordList?.querySelector('.kc-record-list > .kc-record');

    if (!firstRecord) {
      if (!summary.hidden) summary.hidden = true;
      return summary;
    }

    if (activeSearchFilters() && latestSignature) {
      if (summary.hidden) summary.hidden = false;
      return summary;
    }

    const name = text(firstRecord.querySelector('.kc-record-heading h3')) || '名称未入力のDRAFT';
    const supplier = text(firstRecord.querySelector('.kc-record-heading p')) || 'Supplier未入力';
    const meta = [...firstRecord.querySelectorAll('.kc-record-meta span')].map(text).filter(Boolean);
    const updated = meta.at(-1) || '';
    const specs = [...firstRecord.querySelectorAll('.kc-material-specs > span')].slice(0, 4).map((item) => ({
      label: text(item.querySelector('small')),
      value: text(item.querySelector('strong'))
    }));
    const meaningfulSpecs = specs.filter(({ value }) => value && !['未入力', '—', '不明'].includes(value));
    const signature = JSON.stringify({ name, supplier, updated, specs });

    if (signature !== latestSignature) {
      const nameNode = summary.querySelector('[data-kc-latest-name]');
      const supplierNode = summary.querySelector('[data-kc-latest-supplier]');
      const timeNode = summary.querySelector('[data-kc-latest-time]');
      const specsNode = summary.querySelector('[data-kc-latest-specs]');
      if (nameNode) nameNode.textContent = name;
      if (supplierNode) supplierNode.textContent = supplier;
      if (timeNode) timeNode.textContent = updated;
      if (specsNode) {
        if (meaningfulSpecs.length) {
          specsNode.replaceChildren(...meaningfulSpecs.map(({ label, value }) => {
            const cell = document.createElement('span');
            const small = document.createElement('small');
            const strong = document.createElement('strong');
            small.textContent = label;
            strong.textContent = value;
            cell.append(small, strong);
            return cell;
          }));
        } else {
          const empty = document.createElement('span');
          empty.className = 'kc-mobile-latest-empty';
          empty.textContent = '番手・混率・品質表示・ゲージは未入力';
          specsNode.replaceChildren(empty);
        }
      }
      latestSignature = signature;
    }

    if (summary.hidden) summary.hidden = false;
    return summary;
  }

  function placeCaptureBeforeBackup() {
    const inbox = document.getElementById('kcInbox');
    const backup = document.getElementById('kcBackupCard');
    if (!inbox || !backup || inbox.parentNode !== backup.parentNode) return;
    if (inbox.nextElementSibling !== backup) backup.parentNode.insertBefore(inbox, backup);
  }

  function arrangeMobileInbox() {
    if (moving) return;
    const inbox = document.getElementById('kcInbox');
    if (!inbox) return;

    const heading = inbox.querySelector('.kc-panel-heading');
    const connectivity = inbox.querySelector('#kcConnectivityStatus');
    const message = inbox.querySelector('#kcInboxMessage');
    const recordList = inbox.querySelector('#kcRecordList');
    if (!heading || !recordList) return;

    const summary = updateLatestSummary(inbox, recordList);
    const actions = currentPrimaryActions(inbox);
    const drawer = ensureSearchDrawer(inbox);
    updateInboxMessageVisibility(inbox);

    moving = true;
    try {
      placeCaptureBeforeBackup();

      if (actions) actions.classList.add('kc-mobile-primary-actions');
      if (connectivity) connectivity.classList.add('kc-mobile-connectivity');

      let anchor = heading;
      [connectivity, summary, actions, drawer, message, recordList].forEach((node) => {
        if (!node) return;
        if (anchor.nextElementSibling !== node) anchor.insertAdjacentElement('afterend', node);
        anchor = node;
      });
    } finally {
      moving = false;
    }
  }

  function queueArrange() {
    if (moving || queued) return;
    queued = true;
    queueMicrotask(() => {
      queued = false;
      arrangeMobileInbox();
    });
  }

  const observer = new MutationObserver(queueArrange);
  observer.observe(root, { childList: true, subtree: true, characterData: true });
  root.addEventListener('input', queueArrange, true);
  root.addEventListener('change', queueArrange, true);
  arrangeMobileInbox();
})();
