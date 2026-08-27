const CACHE_NAME = 'kc-photo-capture-independent-v11-v2144-safe-launch';
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './sw-register.js',
  './layout-priority.js',
  './exhibition-burst-mode.css',
  './exhibition-burst-mode.js',
  './mobile-compact-20260827.css',
  './mobile-compact-20260827.js',
  './auth-legacy-compat-20260827.js',
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

const NETWORK_TIMEOUT_MS = 5000;

async function fetchWithTimeout(request) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), NETWORK_TIMEOUT_MS);
  try {
    return await fetch(request, { cache: 'no-store', signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

async function networkFirst(request, navigationFallback = false) {
  try {
    const response = await fetchWithTimeout(request);
    if (response.ok) {
      const copy = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, copy)).catch(() => {});
    }
    return response;
  } catch (_error) {
    const cached = await caches.match(request, { ignoreSearch: true });
    if (cached) return cached;
    if (navigationFallback) {
      const fallback = await caches.match('./index.html');
      if (fallback) return fallback;
    }
    return Response.error();
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(
      keys.filter((key) => key.startsWith('kc-photo-capture-independent-') && key !== CACHE_NAME)
        .map((key) => caches.delete(key))
    );
    // Never navigate clients from inside activate. On Android WebAPK/PWA this can
    // deadlock the first navigation and leave the generated splash screen visible.
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin) return;

  if (event.request.mode === 'navigate') {
    event.respondWith(networkFirst(event.request, true));
    return;
  }

  event.respondWith(networkFirst(event.request, false));
});
