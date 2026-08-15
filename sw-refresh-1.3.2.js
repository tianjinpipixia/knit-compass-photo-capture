(() => {
  'use strict';

  const SCRIPT_URL = './sw.js?v=1.3.3-operational-hardening-4';
  const RELOAD_MARKER = 'kc_sw_refresh_1_3_3_operational_hardening_1';

  if (!('serviceWorker' in navigator) || !['http:', 'https:'].includes(location.protocol)) return;

  window.addEventListener('load', () => {
    const hadController = Boolean(navigator.serviceWorker.controller);
    setTimeout(async () => {
      try {
        const registration = await navigator.serviceWorker.register(SCRIPT_URL);
        await registration.update();
        if (!hadController) return;

        const reloadWithCurrentAssets = () => {
          if (sessionStorage.getItem(RELOAD_MARKER)) return;
          sessionStorage.setItem(RELOAD_MARKER, '1');
          location.reload();
        };

        if (navigator.serviceWorker.controller?.scriptURL.includes('1.3.3-operational-hardening-4')) {
          reloadWithCurrentAssets();
          return;
        }
        navigator.serviceWorker.addEventListener('controllerchange', reloadWithCurrentAssets, { once: true });
      } catch (error) {
        console.warn('Photo Captureの更新確認に失敗しました。', error);
      }
    }, 0);
  });
})();
