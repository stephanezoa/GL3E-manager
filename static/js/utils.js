/**
 * GL3E Project Manager Utilities
 */

// Toast Notification System
const Toast = {
    show: (message, type = 'info') => {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} slide-in`;
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
};

// Formatting Utilities
const Format = {
    phone: (number) => {
        // Format Cameroun phone number: 6XX XX XX XX
        const cleaned = ('' + number).replace(/\D/g, '');
        const match = cleaned.match(/^(\d{3})(\d{2})(\d{2})(\d{2})$/);
        if (match) {
            return `${match[1]} ${match[2]} ${match[3]} ${match[4]}`;
        }
        return number;
    },
    
    date: (dateString) => {
        const options = { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' };
        return new Date(dateString).toLocaleDateString('fr-FR', options);
    }
};

// API Helper
const API = {
    async request(url, options = {}) {
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.detail || 'Une erreur est survenue');
            }
            
            return data;
        } catch (error) {
            Toast.show(error.message, 'error');
            throw error;
        }
    }
};
