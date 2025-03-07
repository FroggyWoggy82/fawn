const API = {
    // Get the VAPID public key from the meta tag
    getVapidPublicKey() {
        const metaTag = document.querySelector('meta[name="vapid-public-key"]');
        if (!metaTag) {
            console.error('VAPID public key meta tag is missing');
            return null;
        }
        
        const vapidKey = metaTag.content;
        console.log('Raw VAPID key:', vapidKey); // Debug log
        
        if (!vapidKey || vapidKey === '') {
            console.error('VAPID public key is empty');
            return null;
        }
        
        // Convert the base64 string to Uint8Array
        try {
            const convertedKey = urlBase64ToUint8Array(vapidKey);
            console.log('Successfully converted key to Uint8Array');
            return convertedKey;
        } catch (error) {
            console.error('Failed to convert VAPID key:', error);
            return null;
        }
    },
    
    // Check if device is mobile (missing in your code)
    isMobileDevice() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    },
    
    // Save push subscription to server
    savePushSubscription(subscription) {
        const tokenEl = document.querySelector('meta[name="csrf-token"]');
        if (!tokenEl) {
            console.error('CSRF token meta tag is missing');
            return Promise.reject('CSRF token missing');
        }
        
        const token = tokenEl.content;
        
        return fetch('/save-subscription/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': token
            },
            body: JSON.stringify(subscription)
        })
        .then(response => response.json())
        .catch(error => {
            console.error('Error saving subscription:', error);
            return { status: 'error', message: error.message };
        });
    }
};

function urlBase64ToUint8Array(base64String) {
    // Add more debugging
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

// Push notification functionality
const PushNotifications = {
    // Initialize push notifications
    init() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.log('Push notifications not supported');
            return Promise.reject('Push notifications not supported');
        }
        
        // Ensure service worker is registered
        this.registerServiceWorker()
            .then(() => {
                // Check if already subscribed
                this.checkSubscription();
                
                // Add event listener to subscribe button if it exists
                const subscribeBtn = document.getElementById('push-subscribe-btn');
                if (subscribeBtn) {
                    subscribeBtn.addEventListener('click', () => this.subscribe());
                }
            })
            .catch(error => {
                console.error('Failed to register service worker:', error);
            });
    },
    
    // Register service worker
    registerServiceWorker() {
        return navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                console.log('Service Worker registered successfully:', registration);
                return registration;
            })
            .catch(error => {
                console.error('Service Worker registration failed:', error);
                throw error;
            });
    },
    
    // Check if already subscribed
    checkSubscription() {
        navigator.serviceWorker.ready
            .then(registration => {
                return registration.pushManager.getSubscription();
            })
            .then(subscription => {
                const subscribeBtn = document.getElementById('push-subscribe-btn');
                if (subscribeBtn) {
                    if (subscription) {
                        subscribeBtn.textContent = 'Notifications Enabled';
                        subscribeBtn.disabled = true;
                    } else {
                        subscribeBtn.textContent = 'Enable Push Notifications';
                        subscribeBtn.disabled = false;
                    }
                }
            });
    },
    
    // Subscribe to push notifications
    subscribe() {
        const applicationServerKey = API.getVapidPublicKey();
        
        if (!applicationServerKey) {
            alert('Push notification setup is incomplete. Contact the administrator.');
            return;
        }
        
        navigator.serviceWorker.ready
            .then(registration => {
                // Create subscription
                const options = {
                    userVisibleOnly: true,
                    applicationServerKey: applicationServerKey
                };
                
                console.log('Subscription options:', options);
                return registration.pushManager.subscribe(options);
            })
            .then(subscription => {
                console.log('Subscription successful:', JSON.stringify(subscription));
                // Send subscription to server using the API
                return API.savePushSubscription(subscription);
            })
            .then(response => {
                if (response.status !== 'success') {
                    throw new Error(response.message || 'Failed to store subscription');
                }
                
                const subscribeBtn = document.getElementById('push-subscribe-btn');
                if (subscribeBtn) {
                    subscribeBtn.textContent = 'Notifications Enabled';
                    subscribeBtn.disabled = true;
                }
                
                alert('Push notifications enabled!');
            })
            .catch(error => {
                console.error('Error enabling push notifications:', error);
                
                // Use the handleSubscriptionError function for specific errors
                if (error.message && error.message.includes('different applicationServerKey')) {
                    handleSubscriptionError(error);
                } else {
                    alert('Failed to enable push notifications: ' + error.message);
                }
            });
    }
};

// Function to handle subscription errors
function handleSubscriptionError(error) {
    console.error('Push subscription error:', error);
    
    // Check if it's the specific error about different applicationServerKey
    if (error.message && error.message.includes('different applicationServerKey')) {
        console.log('Attempting to unsubscribe and resubscribe...');
        
        // Get the current registration and unsubscribe
        navigator.serviceWorker.ready
            .then(registration => {
                return registration.pushManager.getSubscription();
            })
            .then(subscription => {
                if (subscription) {
                    return subscription.unsubscribe();
                }
            })
            .then(successful => {
                if (successful) {
                    console.log('Successfully unsubscribed, attempting to resubscribe...');
                    // Reload the page to trigger a fresh subscription
                    window.location.reload();
                }
            })
            .catch(error => {
                console.error('Error during unsubscribe process:', error);
            });
    }
}

// Initialize push notifications when the page loads
document.addEventListener('DOMContentLoaded', () => {
    PushNotifications.init();
});