// API helper functions
const API = {
    // Notification endpoints
    async testNotification(notificationId) {
        try {
            const response = await fetch(`/api/notifications/${notificationId}/test/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error testing notification:', error);
            throw error;
        }
    },

    // Helper function to get CSRF token
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
};