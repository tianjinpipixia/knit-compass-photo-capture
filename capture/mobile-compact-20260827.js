(() => {
  'use strict';

  const FILTER_IDS = [
    'kcSearchAll',
    'kcSearchSupplier',
    'kcSearchYarnName',
    'kcSearchAbbreviation',
    'kcSearchSeason'
  ];
  const EMPTY_VALUES = new Set(['', '未入力', '—', '不明']);
  const root = document.getElementById('app');
  if (!root) return;

  let queued = false;

  function text(node) {
    return String(node?.textContent || '').trim();
  }

  function hasActiveSearch() {
    return FILTER_IDS.some((id) => String(document.getElementById(id)?.value || '').trim());
  }

  function compactLatestSummary() {
    const summary = document.getElementById('kcLatestCaptureSummary');
    if (!summary) return;
    summary.dataset.compactPatch = '20260827-2';

    const specs = summary.querySelector('[data-kc-latest-specs]');
    if (!specs) return;

    const cells = [...specs.children].filter((node) => node.matches?.('span:not(.kc-mobile-latest-empty)'));
    const meaningful = cells.filter((cell) => !EMPTY_VALUES.has(text(cell.querySelector('strong'))));

    if (meaningful.length === 0) {
      const currentEmpty = specs.children.length === 1
        && specs.firstElementChild?.classList.contains('kc-mobile-latest-empty')
        && text(specs.firstElementChild) === '番手・混率・品質表示・ゲージは未入力';
      if (currentEmpty) return;
      const empty = document.createElement('span');
      empty.className = 'kc-mobile-latest-empty';
      empty.textContent = '番手・混率・品質表示・ゲージは未入力';
      specs.replaceChildren(empty);
      return;
    }

    const needsCompaction = specs.children.length !== meaningful.length
      || meaningful.some((node, index) => specs.children[index] !== node);
    if (needsCompaction) specs.replaceChildren(...meaningful);
  }

  function hideDuplicateStatus() {
    const message = document.getElementById('kcInboxMessage');
    if (!message) return;
    const matched = text(message).match(/^保存済み(\d+)件\s*\/\s*検索結果(\d+)件。最新値を表示しています。$/);
    message.hidden = Boolean(!hasActiveSearch() && matched && matched[1] === matched[2]);
  }

  function markPatchVersion() {
    const version = document.querySelector('.kc-build-info strong');
    if (version && !text(version).includes('UI 4')) {
      version.textContent = `${text(version).replace(/\s·\sUI\s\d+$/, '')} · UI 4`;
    }
  }

  function applyPatch() {
    compactLatestSummary();
    hideDuplicateStatus();
    markPatchVersion();
  }

  function queuePatch() {
    if (queued) return;
    queued = true;
    queueMicrotask(() => {
      queued = false;
      applyPatch();
    });
  }

  const observer = new MutationObserver(queuePatch);
  observer.observe(root, { childList: true, subtree: true, characterData: true });
  root.addEventListener('input', queuePatch, true);
  root.addEventListener('change', queuePatch, true);
  applyPatch();
})();
