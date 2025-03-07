// Single unified push notifications script
document.addEventListener('DOMContentLoaded', function() {
    // Utility functions
    function urlBase64ToUint8Array(base64String) {
        console.log('Converting base64 string:', base64String);
        console.log('String length:', base64String.length);
        
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        console.log('After padding and replacement:', base64);
        
        try {
            const rawData = window.atob(base64);
            console.log('Successfully decoded base64, length:', rawData.length);
            
            const outputArray = new Uint8Array(rawData.length);
            
            for (let i = 0; i < rawData.length; ++i) {
                outputArray[i] = rawData.charCodeAt(i);
            }
            return outputArray;
        } catch (error) {
            console.error('Error decoding base64:', error);
            throw error;
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Consolidated API object
    const API = {
        getVapidPublicKey: function() {
            // First try to get from inline script variable if available
            if (typeof vapidPublicKey !== 'undefined' && vapidPublicKey) {
                console.log('Using inline VAPID key:', vapidPublicKey);
                return vapidPublicKey;
            }
            
            // Then try meta tag
            const metaTag = document.querySelector('meta[name="vapid-public-key"]');
            if (metaTag && metaTag.content) {
                console.log('Using VAPID key from meta tag:', metaTag.content);
                return metaTag.content;
            }
            
            console.error('VAPID public key not found');
            return null;
        },
        
        isMobileDevice: function() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        },
        
        savePushSubscription: function(subscription) {
            return fetch('/push/subscribe/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    subscription: subscription
                })
            }).then(response => response.json());
        },
        
        testNotification: function(id) {
            return fetch(`/api/notifications/${id}/test/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'Content-Type': 'application/json'
                }
            }).then(response => response.json());
        }
    };

    // Request notification permission
    function requestNotificationPermission() {
        return new Promise((resolve, reject) => {
            if (!('Notification' in window)) {
                alert('This browser does not support desktop notification');
                reject('Notifications not supported');
            } else if (Notification.permission === 'granted') {
                resolve();
            } else if (Notification.permission !== 'denied') {
                Notification.requestPermission().then(permission => {
                    if (permission === 'granted') {
                        resolve();
                    } else {
                        reject('Notification permission denied');
                    }
                });
            } else {
                reject('Notification permission denied');
            }
        });
    }

    // Single service worker registration function
    function registerServiceWorker() {
        return navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                console.log('ServiceWorker registration successful with scope: ', registration.scope);
                return registration;
            })
            .catch(error => {
                console.error('ServiceWorker registration failed: ', error);
                throw error;
            });
    }

    // Push subscription function
    function subscribeToPushNotifications() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.log('Push notifications not supported');
            return Promise.reject('Push notifications not supported');
        }

        return registerServiceWorker()
            .then(() => requestNotificationPermission())
            .then(() => navigator.serviceWorker.ready)
            .then(registration => {
                console.log('Service worker ready, getting subscription...');
                return registration.pushManager.getSubscription();
            })
            .then(subscription => {
                if (subscription) {
                    console.log('Already subscribed to push notifications');
                    return subscription;
                }
                
                console.log('Creating new subscription...');
                const vapidPublicKey = API.getVapidPublicKey();
                if (!vapidPublicKey) {
                    throw new Error('VAPID public key not available');
                }
                
                console.log('Using VAPID key:', vapidPublicKey);
                const applicationServerKey = urlBase64ToUint8Array(vapidPublicKey);
                console.log('Converted to Uint8Array:', applicationServerKey);
                
                return navigator.serviceWorker.ready.then(registration => {
                    return registration.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: applicationServerKey
                    });
                });
            })
            .then(subscription => {
                console.log('Subscription object:', JSON.stringify(subscription));
                console.log('Saving push subscription...');
                return API.savePushSubscription(subscription);
            })
            .then(response => {
                console.log('Push subscription saved:', response);
                return response;
            });
    }

    // Unsubscribe and resubscribe if needed
    function handleSubscriptionError(error) {
        console.error('Push subscription error:', error);
        
        if (error.message && error.message.includes('different applicationServerKey')) {
            console.log('Attempting to unsubscribe and resubscribe...');
            
            return navigator.serviceWorker.ready
                .then(registration => registration.pushManager.getSubscription())
                .then(subscription => {
                    if (subscription) {
                        return subscription.unsubscribe();
                    }
                    return false;
                })
                .then(successful => {
                    if (successful) {
                        console.log('Successfully unsubscribed, attempting to resubscribe...');
                        return subscribeToPushNotifications();
                    }
                    return null;
                });
        }
        
        return Promise.reject(error);
    }

    // Add event listener to subscribe button
    const pushSubscribeBtn = document.getElementById('push-subscribe-btn');
    if (pushSubscribeBtn) {
        pushSubscribeBtn.addEventListener('click', function() {
            subscribeToPushNotifications()
                .then(response => {
                    alert('Push notifications enabled successfully!');
                    pushSubscribeBtn.textContent = 'Notifications Enabled';
                    pushSubscribeBtn.disabled = true;
                })
                .catch(error => {
                    console.error('Error enabling push notifications:', error);
                    
                    if (error.message && error.message.includes('different applicationServerKey')) {
                        return handleSubscriptionError(error)
                            .then(result => {
                                if (result) {
                                    alert('Push notifications enabled successfully!');
                                    pushSubscribeBtn.textContent = 'Notifications Enabled';
                                    pushSubscribeBtn.disabled = true;
                                }
                            })
                            .catch(error => {
                                alert('Failed to enable push notifications: ' + error.message);
                            });
                    } else {
                        alert('Failed to enable push notifications: ' + error.message);
                    }
                });
        });
    }

    // Initialize push notifications automatically for mobile
    if (API.isMobileDevice() && 'serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.ready
            .then(registration => registration.pushManager.getSubscription())
            .then(subscription => {
                if (!subscription) {
                    console.log('Mobile device detected, attempting auto-subscription');
                    return subscribeToPushNotifications()
                        .then(() => {
                            if (pushSubscribeBtn) {
                                pushSubscribeBtn.textContent = 'Notifications Enabled';
                                pushSubscribeBtn.disabled = true;
                            }
                        })
                        .catch(error => {
                            console.error('Auto-subscription failed:', error);
                        });
                } else if (pushSubscribeBtn) {
                    pushSubscribeBtn.textContent = 'Notifications Enabled';
                    pushSubscribeBtn.disabled = true;
                }
            });
    }

    // Correctly wire up test notification buttons
    document.querySelectorAll('.test-notification-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.dataset.id;
            API.testNotification(id)
                .then(data => {
                    if (data.status === 'success') {
                        if (API.isMobileDevice()) {
                            // On mobile, just show an alert instead of a web notification
                            alert(`${data.title}\n\n${data.message}`);
                        } else {
                            requestNotificationPermission().then(() => {
                                showNotification(data.title, data.message);
                            });
                        }
                    } else {
                        alert('Error testing notification');
                    }
                })
                .catch(error => {
                    console.error('Test notification error:', error);
                    alert('Error testing notification: ' + error.message);
                });
        });
    });

    // Show notification function
    function showNotification(title, message) {
        if (Notification.permission === 'granted') {
            const notification = new Notification(title, {
                body: message,
                icon: '/static/meals/images/notification-icon.png',
                badge: '/static/meals/images/notification-badge.png'
            });
            
            notification.onclick = function() {
                window.focus();
                this.close();
            };
            
            // Auto close after 5 seconds
            setTimeout(() => {
                notification.close();
            }, 5000);
        }
    }

    // Store VAPID key globally for any inline scripts to use
    window.vapidPublicKey = API.getVapidPublicKey();
});