(() => {
  'use strict';
  if (!('serviceWorker' in navigator) || !['http:', 'https:'].includes(location.protocol)) return;
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js?v=2.1.44-independent.3', { scope: './' })
      .then((registration) => registration.update())
      .catch((error) => console.warn('Photo Captureのオフライン準備に失敗しました。', error));
  });
})();
