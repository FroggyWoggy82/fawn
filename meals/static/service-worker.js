// Service worker for notifications
self.addEventListener('install', function(event) {
    self.skipWaiting();
});
  
self.addEventListener('activate', function(event) {
    return self.clients.claim();
});
  
self.addEventListener('fetch', function(event) {
    event.respondWith(fetch(event.request));
});

// Handle push notifications
self.addEventListener('push', function(event) {
    let data = {};
    if (event.data) {
        data = event.data.json();
    }
    
    const title = data.title || 'Notification';
    const options = {
        body: data.message || 'You have a new notification',
        icon: '/static/meals/images/notification-icon.png',
        badge: '/static/meals/images/notification-badge.png',
        data: {
            url: data.url || '/'
        }
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification click
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});