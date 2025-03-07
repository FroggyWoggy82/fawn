// Service worker for notifications with iOS Safari support
self.addEventListener('install', function(event) {
    self.skipWaiting();
    console.log('Service Worker installed');
});
  
self.addEventListener('activate', function(event) {
    console.log('Service Worker activated');
    return self.clients.claim();
});

// Basic offline caching strategy
self.addEventListener('fetch', function(event) {
    // You can implement more sophisticated caching here if needed
    event.respondWith(
        fetch(event.request).catch(function() {
            return caches.match(event.request);
        })
    );
});

// Handle push notifications with better iOS Safari support
self.addEventListener('push', function(event) {
    console.log('Push notification received', event);
    
    // iOS Safari requires careful payload handling
    let data = {};
    try {
        if (event.data) {
            // Try multiple approaches to handle different browser implementations
            if (typeof event.data.text === 'function') {
                const textData = event.data.text();
                try {
                    data = JSON.parse(textData);
                } catch (e) {
                    data = { message: textData };
                }
            } else if (typeof event.data.json === 'function') {
                data = event.data.json();
            } else {
                data = { message: 'New notification' };
            }
        }
    } catch (e) {
        console.error('Error parsing notification data', e);
        data = { message: 'New notification' };
    }
    
    console.log('Parsed notification data:', data);
    
    const title = data.title || 'Notification';
    const options = {
        body: data.message || data.body || 'You have a new notification',
        icon: data.icon || '/static/meals/images/notification-icon.png',
        badge: data.badge || '/static/meals/images/notification-badge.png',
        tag: data.tag || 'default',
        data: {
            url: data.url || '/'
        },
        // Add vibration pattern for mobile devices
        vibrate: [200, 100, 200],
        // For iOS: make notifications persistent until interaction
        requireInteraction: true,
        // Additional actions (buttons) if supported
        actions: data.actions || [
            {
                action: 'view',
                title: 'View'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Handle notification click with improved navigation
self.addEventListener('notificationclick', function(event) {
    console.log('Notification clicked', event);
    event.notification.close();
    
    const urlToOpen = event.notification.data && event.notification.data.url ? 
                      event.notification.data.url : '/';
    
    // Handle action buttons if clicked
    if (event.action === 'view') {
        console.log('View action clicked');
    }
    
    // Navigate to URL - with better focus handling for existing windows
    event.waitUntil(
        clients.matchAll({
            type: 'window',
            includeUncontrolled: true
        }).then(function(clientList) {
            // Check if there's already a window/tab open with the target URL
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url === urlToOpen && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // If no existing window, open a new one
            if (clients.openWindow) {
                return clients.openWindow(urlToOpen);
            }
        })
    );
});

// Optional: Handle notification close event
self.addEventListener('notificationclose', function(event) {
    console.log('Notification closed', event);
});