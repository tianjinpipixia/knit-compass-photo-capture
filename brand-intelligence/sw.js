const CACHE_NAME = 'kc-brand-intelligence-v0-4-7-sales-nav-4';
const APP_SHELL = [
  './',
  './index.html',
  './index-current.html',
  './app.html',
  './manifest.webmanifest',
  '../brand/knit-compass-mark.png',
  './yarn-glossary.html',
  './data/cn-yarn-glossary.json',
  './data/cn-yarn-glossary.json?v=1.0.0'
];

const scopeUrl = new URL(self.registration.scope);
const shellPaths = new Set(APP_SHELL.map(path => new URL(path, scopeUrl).pathname));

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(key => key.startsWith('kc-brand-intelligence-') && key !== CACHE_NAME).map(key => caches.delete(key))))
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

  event.respondWith(fetch(event.request).then(response => {
    const copy = response.clone();
    caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
    return response;
  }).catch(() => caches.match(event.request, { ignoreSearch: true })));
});
