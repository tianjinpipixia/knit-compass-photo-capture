(() => {
  'use strict';

  const SCRIPT_URL = './sw.js?v=1.3.5-current-ui-direct-entry';
  const RELOAD_MARKER = 'kc_sw_refresh_1_3_4_direct_form_order_mobile_actions';

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

        if (navigator.serviceWorker.controller?.scriptURL.includes('1.3.5-current-ui-direct-entry')) {
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
