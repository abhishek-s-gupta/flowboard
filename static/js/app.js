/**
 * Flowboard App Core Module
 * Minimal, calm, responsive, robust fetch() wrapper with CSRF.
 */

(function () {
  'use strict';

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

  async function fetchJSON(url, data = null, method = 'POST') {
    const options = {
      method: data && method === 'GET' ? 'GET' : method,
      headers: {
        'X-CSRFToken': getCookie('csrftoken') || '',
        'X-Requested-With': 'XMLHttpRequest',
      },
    };

    if (data && options.method !== 'GET') {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    if (!response.ok) {
      let errorMsg = `Server error (${response.status})`;
      try {
        const errJson = await response.json();
        if (errJson.message) errorMsg = errJson.message;
      } catch (e) {
        // non-JSON error
      }
      const err = new Error(errorMsg);
      err.status = response.status;
      throw err;
    }
    return await response.json();
  }

  function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'toast-error' : ''}`;
    toast.innerHTML = `
      <span>${escapeHTML(message)}</span>
      <button type="button" class="icon-btn btn-sm" aria-label="Dismiss toast" style="color: inherit;">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    `;

    const closeBtn = toast.querySelector('button');
    closeBtn.addEventListener('click', () => toast.remove());

    container.appendChild(toast);
    setTimeout(() => {
      if (toast.parentElement) toast.remove();
    }, 3800);
  }

  function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }

  function updateBadgeCount(count) {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;
    if (count > 0) {
      badge.textContent = count > 99 ? '99+' : count;
      badge.style.display = 'flex';
    } else {
      badge.style.display = 'none';
      badge.textContent = '0';
    }
  }

  // Theme Management
  function initTheme() {
    const savedTheme = localStorage.getItem('flowboard_theme') || document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(savedTheme);

    const toggleBtn = document.getElementById('themeToggleBtn');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        applyTheme(newTheme);
        localStorage.setItem('flowboard_theme', newTheme);

        // Sync with backend profile if logged in
        fetchJSON('/accounts/api/profile/update/', { theme_preference: newTheme }).catch(() => {});
      });
    }
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const sunIcon = document.getElementById('themeIconSun');
    const moonIcon = document.getElementById('themeIconMoon');
    if (sunIcon && moonIcon) {
      if (theme === 'dark') {
        sunIcon.style.display = 'block';
        moonIcon.style.display = 'none';
      } else {
        sunIcon.style.display = 'none';
        moonIcon.style.display = 'block';
      }
    }
  }

  // Global UI Setup
  function initUI() {
    // Mobile sidebar toggle
    const openBtn = document.getElementById('sidebarOpenBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.getElementById('appSidebar');

    if (openBtn && sidebar) {
      openBtn.addEventListener('click', () => sidebar.classList.add('open'));
    }
    if (closeBtn && sidebar) {
      closeBtn.addEventListener('click', () => sidebar.classList.remove('open'));
    }

    // Modal: Create Project
    const openModalBtn = document.getElementById('btnOpenNewProjectModal');
    const modal = document.getElementById('createProjectModal');
    const closeModalBtn = document.getElementById('closeCreateProjectModal');
    const cancelModalBtn = document.getElementById('cancelCreateProject');

    if (openModalBtn && modal) {
      openModalBtn.addEventListener('click', () => modal.classList.add('open'));
    }
    if (closeModalBtn && modal) {
      closeModalBtn.addEventListener('click', () => modal.classList.remove('open'));
    }
    if (cancelModalBtn && modal) {
      cancelModalBtn.addEventListener('click', () => modal.classList.remove('open'));
    }

    // Close on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
        const drawer = document.getElementById('taskDetailDrawer');
        if (drawer && drawer.classList.contains('open')) {
          drawer.classList.remove('open');
        }
        const dropdown = document.getElementById('notificationsDropdown');
        if (dropdown && dropdown.classList.contains('open')) {
          dropdown.classList.remove('open');
        }
      }
    });

    // Close modal on background click
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
      overlay.addEventListener('click', (e) => {
        if (e.target === overlay) overlay.classList.remove('open');
      });
    });

    // Fast demo login fill button on login page
    const fillDemoBtn = document.getElementById('btnFillDemoCredentials');
    if (fillDemoBtn) {
      fillDemoBtn.addEventListener('click', () => {
        const u = document.getElementById('id_username');
        const p = document.getElementById('id_password');
        if (u) u.value = 'alex';
        if (p) p.value = 'password123';
      });
    }
  }

  window.FlowboardApp = {
    fetchJSON,
    showToast,
    escapeHTML,
    getCookie,
    updateBadgeCount,
  };

  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initUI();
  });
})();
