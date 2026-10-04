/**
 * NyayaAI - Global Application Scripts
 * Manages toast notifications, responsive mobile sidebar, and global UI components.
 */

// Toast notification helper
window.showToast = function(message, type = 'info', duration = 4000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');

    let iconSvg = '';
    if (type === 'success') {
        iconSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    } else if (type === 'error') {
        iconSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12.01" y2="8"></line><line x1="12" y1="12" x2="12" y2="16"></line></svg>';
    } else {
        iconSvg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
    }

    toast.innerHTML = `
        <div class="toast-icon">${iconSvg}</div>
        <div class="toast-message">${message}</div>
        <button type="button" class="toast-close" aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
        </button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
        removeToast(toast);
    });

    container.appendChild(toast);

    // Auto dismiss
    setTimeout(() => {
        removeToast(toast);
    }, duration);
};

function removeToast(toast) {
    if (!toast || !toast.parentElement) return;
    toast.classList.add('toast-hiding');
    setTimeout(() => {
        if (toast.parentElement) toast.remove();
    }, 300);
}

// Auto dismiss existing flash toasts
document.addEventListener('DOMContentLoaded', function() {
    const existingToasts = document.querySelectorAll('.toast');
    existingToasts.forEach(toast => {
        setTimeout(() => {
            removeToast(toast);
        }, 4500);
    });

    // Mobile Sidebar Drawer Toggle
    const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    const appSidebar = document.getElementById('app-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');

    if (mobileMenuToggle && appSidebar) {
        mobileMenuToggle.addEventListener('click', () => {
            appSidebar.classList.toggle('sidebar-open');
            if (backdrop) backdrop.classList.toggle('backdrop-active');
        });

        if (backdrop) {
            backdrop.addEventListener('click', () => {
                appSidebar.classList.remove('sidebar-open');
                backdrop.classList.remove('backdrop-active');
            });
        }
    }

    // Password Visibility Toggles
    document.querySelectorAll('.btn-password-toggle').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.dataset.target;
            const input = document.getElementById(targetId);
            if (!input) return;

            const eyeOpen = this.querySelector('.eye-open');
            const eyeClosed = this.querySelector('.eye-closed');

            if (input.type === 'password') {
                input.type = 'text';
                if (eyeOpen) eyeOpen.style.display = 'none';
                if (eyeClosed) eyeClosed.style.display = 'block';
            } else {
                input.type = 'password';
                if (eyeOpen) eyeOpen.style.display = 'block';
                if (eyeClosed) eyeClosed.style.display = 'none';
            }
        });
    });
});
