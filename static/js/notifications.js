/**
 * Flowboard Notifications Module
 * Real-time WebSocket delivery, notification bell badge, and dropdown.
 */

(function () {
  'use strict';

  let notificationSocket = null;

  function initNotifications() {
    const bellBtn = document.getElementById('notificationBellBtn');
    const dropdown = document.getElementById('notificationsDropdown');
    const dropdownList = document.getElementById('notificationsDropdownList');
    const markAllBtn = document.getElementById('btnMarkAllReadDropdown');

    if (!bellBtn || !dropdown) return;

    // Toggle dropdown
    bellBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isOpen = dropdown.classList.contains('open');
      if (!isOpen) {
        dropdown.classList.add('open');
        loadDropdownNotifications();
      } else {
        dropdown.classList.remove('open');
      }
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!dropdown.contains(e.target) && !bellBtn.contains(e.target)) {
        dropdown.classList.remove('open');
      }
    });

    // Mark all read in dropdown
    if (markAllBtn) {
      markAllBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        markAllBtn.disabled = true;
        try {
          const res = await window.FlowboardApp.fetchJSON('/notifications/api/read-all/');
          if (res.status === 'ok') {
            window.FlowboardApp.updateBadgeCount(0);
            dropdownList.querySelectorAll('.notification-item.unread').forEach(item => {
              item.classList.remove('unread');
            });
          }
        } catch (err) {
          window.FlowboardApp.showToast('Failed to mark all as read', 'error');
        } finally {
          markAllBtn.disabled = false;
        }
      });
    }

    // Connect WebSocket
    notificationSocket = new window.FlowboardSocket(
      '/ws/notifications/',
      (data) => {
        if (data.type === 'notification') {
          handleIncomingNotification(data);
        }
      }
    );
  }

  async function loadDropdownNotifications() {
    const dropdownList = document.getElementById('notificationsDropdownList');
    if (!dropdownList) return;

    try {
      const data = await window.FlowboardApp.fetchJSON('/notifications/api/dropdown/', null, 'GET');
      window.FlowboardApp.updateBadgeCount(data.unread_count);

      if (!data.notifications || data.notifications.length === 0) {
        dropdownList.innerHTML = `
          <div style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 13px;">
            No notifications
          </div>
        `;
        return;
      }

      dropdownList.innerHTML = data.notifications.map(n => renderNotificationItemHTML(n)).join('');
      attachDropdownItemHandlers();
    } catch (err) {
      dropdownList.innerHTML = `
        <div style="padding: 16px; text-align: center; color: var(--danger); font-size: 12px;">
          Failed to load notifications
        </div>
      `;
    }
  }

  function renderNotificationItemHTML(n) {
    const link = n.project_id
      ? `/projects/${n.project_id}/${n.task_id ? `?task=${n.task_id}` : ''}`
      : '#';

    return `
      <div class="notification-item ${!n.is_read ? 'unread' : ''}" data-id="${n.id}" id="dropdownNotif-${n.id}">
        <div style="flex: 1; min-width: 0;">
          <div style="display: flex; align-items: baseline; justify-content: space-between; gap: 8px;">
            <a href="${link}" style="font-size: 12px; font-weight: 600; color: var(--text-primary); text-decoration: none; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
              ${window.FlowboardApp.escapeHTML(n.title)}
            </a>
            <span style="font-size: 11px; color: var(--text-muted); flex-shrink: 0;">${n.created_at}</span>
          </div>
          <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin-top: 3px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
            ${window.FlowboardApp.escapeHTML(n.message)}
          </div>
        </div>
        ${!n.is_read ? `
          <button type="button" class="icon-btn btn-sm btn-mark-read-dropdown" data-id="${n.id}" title="Mark read" aria-label="Mark read" style="flex-shrink: 0; width: 22px; height: 22px;">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
          </button>
        ` : ''}
      </div>
    `;
  }

  function attachDropdownItemHandlers() {
    document.querySelectorAll('.btn-mark-read-dropdown').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const id = btn.dataset.id;
        btn.disabled = true;
        try {
          const res = await window.FlowboardApp.fetchJSON(`/notifications/api/${id}/read/`);
          if (res.status === 'ok') {
            const item = document.getElementById(`dropdownNotif-${id}`);
            if (item) item.classList.remove('unread');
            btn.remove();
            window.FlowboardApp.updateBadgeCount(res.unread_count);
          }
        } catch (err) {
          btn.disabled = false;
        }
      });
    });
  }

  function handleIncomingNotification(data) {
    window.FlowboardApp.updateBadgeCount(data.unread_count);

    const n = data.notification;
    if (n) {
      window.FlowboardApp.showToast(`${n.title}: ${n.message}`);

      const dropdownList = document.getElementById('notificationsDropdownList');
      if (dropdownList && !dropdownList.querySelector('#notificationsLoading')) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = renderNotificationItemHTML(n);
        const newItem = tempDiv.firstElementChild;
        dropdownList.prepend(newItem);
        attachDropdownItemHandlers();
      }
    }
  }

  document.addEventListener('DOMContentLoaded', initNotifications);
})();
