const CACHE_NAME = 'kc-photo-capture-independent-v8-v2144-compact-summary';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './sw-register.js',
  './layout-priority.js',
  './exhibition-burst-mode.css',
  './exhibition-burst-mode.js',
  '../app.css',
  '../knit-compass-ui.css',
  '../connection-status.css',
  '../app.js',
  '../exhibition-supplier-master.js',
  '../backup.js',
  '../usage-metrics.js',
  '../yarn-taxonomy-guard.js',
  '../brand/knit-compass-mark.png',
  '../icon-192.png',
  '../icon-512.png',
  '../icon-maskable-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.filter((key) => key.startsWith('kc-photo-capture-independent-') && key !== CACHE_NAME)
        .map((key) => caches.delete(key))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('./index.html'))
    );
    return;
  }

  event.respondWith(
    fetch(event.request).then((response) => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
      }
      return response;
    }).catch(() => caches.match(event.request, { ignoreSearch: true }))
  );
});
