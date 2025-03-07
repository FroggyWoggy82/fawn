// Minimal service worker - progressive enhancement approach
self.addEventListener('install', function(event) {
    self.skipWaiting();
    console.log('Service Worker installed');
});

self.addEventListener('activate', function(event) {
    event.waitUntil(self.clients.claim());
    console.log('Service Worker activated');
});

// Simple pass-through fetch handler
self.addEventListener('fetch', function(event) {
    event.respondWith(fetch(event.request));
});

// Handle push notifications
self.addEventListener('push', function(event) {
    let data = {};
    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (e) {
        data = { title: 'New Notification', message: 'You have a new notification' };
    }
    
    const title = data.title || 'Notification';
    const options = {
        body: data.message || 'You have a new notification',
        icon: '/static/meals/images/notification-icon.png',
        badge: '/static/meals/images/notification-badge.png'
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification click
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    event.waitUntil(
        clients.openWindow('/')
    );
});