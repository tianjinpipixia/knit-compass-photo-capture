(() => {
  'use strict';

  const root = document.getElementById('app');
  if (!root) return;

  let moving = false;

  function placeCaptureBeforeBackup() {
    if (moving) return;
    const inbox = document.getElementById('kcInbox');
    const backup = document.getElementById('kcBackupCard');
    if (!inbox || !backup || inbox.parentNode !== backup.parentNode) return;
    if (inbox.nextElementSibling === backup) return;

    moving = true;
    backup.parentNode.insertBefore(inbox, backup);
    moving = false;
  }

  const observer = new MutationObserver(() => queueMicrotask(placeCaptureBeforeBackup));
  observer.observe(root, { childList: true, subtree: true });
  placeCaptureBeforeBackup();
})();
