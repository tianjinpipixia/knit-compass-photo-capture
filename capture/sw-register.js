(() => {
  'use strict';
  if (!('serviceWorker' in navigator) || !['http:', 'https:'].includes(location.protocol)) return;

  const SW_VERSION = '2.1.44-independent.6-safe-launch';
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
      .catch((error) => console.warn('Photo Captureのオフライン準備に失敗しました。', error));
  });
})();
