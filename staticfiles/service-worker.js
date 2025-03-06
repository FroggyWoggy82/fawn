// Simple service worker that does nothing but prevent 404 errors
self.addEventListener('install', function(event) {
    self.skipWaiting();
  });
  
  self.addEventListener('activate', function(event) {
    return self.clients.claim();
  });
  
  self.addEventListener('fetch', function(event) {
    event.respondWith(fetch(event.request));
  });