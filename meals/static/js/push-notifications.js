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
                    // Use the VAPID key from the API
                    applicationServerKey: API.getVapidPublicKey()
                };
                
                return registration.pushManager.subscribe(options);
            })
            .then(subscription => {
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
    if (typeof API !== 'undefined' && API.isMobileDevice()) {
        PushNotifications.init();
    }
});