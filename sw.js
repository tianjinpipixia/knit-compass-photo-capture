const CACHE_NAME = 'kc-photo-capture-v1-3-1-navigation-7';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './app.css',
  './connection-status.css',
  './photo-capture-card-progress-v1.css',
  './app.js',
  './knitting-ends-field.js',
  './photo-capture-card-progress-v1.js',
  './backup.js',
  './app-state-guard.js',
  './icon.svg',
  './icon-180.png',
  './icon-192.png',
  './icon-512.png',
  './icon-maskable-512.png',
  './brand-intelligence/',
  './brand-intelligence/index.html',
  './brand-intelligence/index-current.html',
  './brand-intelligence/app.html',
  './brand-intelligence/yarn-glossary.html',
  './brand-intelligence/data/cn-yarn-glossary.json',
  './brand-intelligence/manifest.webmanifest',
  './brand-intelligence/icon.svg',
  './owner-yarns/',
  './owner-yarns/index.html',
  './knit-image/',
  './knit-image/index.html',
  './knit-image/app.css',
  './knit-image/app.js',
  './data/yarn-catalog/mz100-catalog-2000.json',
  './data/manual-intake/2026-08-08-weijie-hesheng-batch1.json',
  './data/manual-intake/2026-08-08-weihai-yaxin-chengyun-batch2.json',
  './data/manual-intake/2026-08-10-mz100-yarn-research-batch3.json',
  './data/manual-intake/2026-08-12-twin-win-company-factory-batch4.json',
  './data/manual-intake/2026-08-12-rope-picnic-gdm56050-batch5.json',
  './fabric-inspection/',
  './fabric-inspection/index.html',
  './fabric-inspection/app.js',
  './market-intelligence/',
  './market-intelligence/index.html',
  './market-intelligence/app.js',
  './daily/',
  './daily/index.html',
  './customer-sharing/',
  './customer-sharing/index.html',
  './customer-sharing/policy.js',
  './stylem/',
  './stylem/index.html',
  './status/',
  './status/index.html',
  './config/system-registry.json'
];

const scopeUrl = new URL(self.registration.scope);
const shellPaths = new Set(APP_SHELL.map(path => new URL(path, scopeUrl).pathname));

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('kc-photo-capture-') && key !== CACHE_NAME).map(key => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== scopeUrl.origin || !shellPaths.has(url.pathname)) return;

  if (event.request.mode === 'navigate') {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request, { ignoreSearch: true }).then(hit => hit || caches.match('./index.html'))));
    return;
  }

  event.respondWith(
    caches.match(event.request, { ignoreSearch: true }).then(cached => cached || fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }))
  );
});
