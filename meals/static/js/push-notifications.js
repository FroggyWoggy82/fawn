// Push notification functionality
const PushNotifications = {
    // Initialize push notifications
    init() {
        if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
            console.log('Push notifications not supported');
            return Promise.reject('Push notifications not supported');
        }
        
        // Check if already subscribed
        this.checkSubscription();
        
        // Add event listener to subscribe button if it exists
        const subscribeBtn = document.getElementById('push-subscribe-btn');
        if (subscribeBtn) {
            subscribeBtn.addEventListener('click', () => this.subscribe());
        }
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
        navigator.serviceWorker.ready
            .then(registration => {
                // Create subscription
                const options = {
                    userVisibleOnly: true,
                    // You'll need to generate VAPID keys for your application
                    // and replace this with your public key
                    applicationServerKey: this.urlBase64ToUint8Array(
                        'BEl62iUYgUivxIkv69yViEuiBIa-Ib9-SkvMeAtA3LFgDzkrxZJjSgSnfckjBJuBkr3qBUYIHBQFLXYp5Nksh8U'
                    )
                };
                
                return registration.pushManager.subscribe(options);
            })
            .then(subscription => {
                // Send subscription to server
                return fetch('/api/push-subscribe/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': API.getCsrfToken()
                    },
                    body: JSON.stringify({
                        subscription: subscription.toJSON()
                    })
                });
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to store subscription');
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
                alert('Failed to enable push notifications: ' + error.message);
            });
    },
    
    // Helper function to convert base64 to Uint8Array
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
};

// Initialize push notifications when the page loads
document.addEventListener('DOMContentLoaded', () => {
    if (API.isMobileDevice()) {
        PushNotifications.init();
    }
});