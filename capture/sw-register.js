(() => {
  'use strict';
  if (!('serviceWorker' in navigator) || !['http:', 'https:'].includes(location.protocol)) return;

  const params = new URLSearchParams(location.search);
  if (params.get('direct') === '1') {
    console.info('Photo Capture direct mode: Service Worker registration skipped.');
    return;
  }

  const SW_VERSION = '2.1.44-independent.13-v04-ui';
  const RELOAD_MARKER = `kc_photo_capture_controller_${SW_VERSION}`;
  let reloading = false;

  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (reloading) return;
    if (sessionStorage.getItem(RELOAD_MARKER) === 'done') return;
    reloading = true;
    sessionStorage.setItem(RELOAD_MARKER, 'done');
    location.reload();
  });

  window.addEventListener('load', () => {
    navigator.serviceWorker.register(`./sw.js?v=${SW_VERSION}`, { scope: './', updateViaCache: 'none' })
      .then((registration) => registration.update())
      .catch(() => {
        // The online screen remains usable even when this browser blocks Service Workers.
      });
  });
})();
