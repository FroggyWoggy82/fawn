// Service Worker for Meal Planner PWA

const CACHE_NAME = 'meal-planner-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/home/',
  '/daily_submission/',
  '/dashboard/',
  '/acne/',
  '/wir/',
  '/meal_planner/',
  '/dish_calculator/',
  '/offline/',
  '/notifications/',  // Add the new notifications URL
  // Add more URLs to cache as needed
];

// Install event - caches initial resources
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Fetch event - return cached assets or fetch from network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }

        // Clone the request because it's a one-time use
        const fetchRequest = event.request.clone();

        return fetch(fetchRequest).then(
          response => {
            // Don't cache if not a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clone the response because it's a one-time use
            const responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(cache => {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        ).catch(() => {
          // If fetch fails (offline), show a fallback page for HTML requests
          if (event.request.headers.get('accept').includes('text/html')) {
            return caches.match('/offline.html');
          }
        });
      })
  );
});
// Push notification event handler
self.addEventListener('push', function(event) {
  console.log('[Service Worker] Push Received.');
  console.log(`[Service Worker] Push had this data: "${event.data.text()}"`);

  try {
    const data = JSON.parse(event.data.text());
    const title = data.title || 'Meal Planner Notification';
    const options = {
      body: data.message || 'You have a new notification',
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-72x72.png',
      data: {
        url: data.url || '/'
      }
    };

    event.waitUntil(self.registration.showNotification(title, options));
  } catch (e) {
    // Fallback for non-JSON data
    const title = 'Meal Planner';
    const options = {
      body: event.data.text(),
      icon: '/static/icons/icon-192x192.png',
      badge: '/static/icons/icon-72x72.png'
    };
    
    event.waitUntil(self.registration.showNotification(title, options));
  }
});

// Notification click event handler
self.addEventListener('notificationclick', function(event) {
  console.log('[Service Worker] Notification click received.');

  event.notification.close();

  // This looks to see if the current is already open and focuses if it is
  event.waitUntil(
    clients.matchAll({
      type: "window"
    })
    .then(function(clientList) {
      const url = event.notification.data && event.notification.data.url ? event.notification.data.url : '/';
      
      for (var i = 0; i < clientList.length; i++) {
        var client = clientList[i];
        if (client.url === url && 'focus' in client)
          return client.focus();
      }
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});