// sw.js
const CACHE = 'flota-static-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  'https://cdn.sheetjs.com/xlsx-latest/package/dist/xlsx.full.min.js',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

// Instala y precachea estáticos
self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
});

// Limpia caches viejos
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
});

// Estrategia: network-first para API, cache-first para estáticos
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  // Llamadas a Apps Script siempre a la red (y caemos a cache si no hay)
  if (url.href.includes('script.google.com/macros')) {
    e.respondWith(fetch(e.request).catch(() => caches.match(e.request)));
    return;
  }

  // Archivos estáticos desde cache
  e.respondWith(caches.match(e.request).then(res => res || fetch(e.request)));
});

