// static/expenses/serviceworker.js - simple cache-first PWA service worker
const CACHE_NAME = 'expense-tracker-v1';
const OFFLINE_URL = '/offline/';

const CACHE_FILES = [
  '/',
  OFFLINE_URL,
  '/static/expenses/styles.css',
  '/static/expenses/manifest.json'
  // add other assets you want cached (icons, chart.js from CDN are not cached)
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(CACHE_FILES))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim());
});

// fetch handler: try network, fallback to cache; for navigation fallback to offline page
self.addEventListener('fetch', function (event) {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match(OFFLINE_URL))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then(function (resp) {
      return resp || fetch(event.request).then(function (response) {
        // cache the response for future requests
        return caches.open(CACHE_NAME).then(function (cache) {
          try { cache.put(event.request, response.clone()); } catch(e) {}
          return response;
        });
      }).catch(() => caches.match(OFFLINE_URL))
    })
  );
});
