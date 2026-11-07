/**
 * Flowboard Board Module
 * Kanban card filtering, task drawer, comments thread, column CRUD, and live board WebSockets.
 */

(function () {
  'use strict';

  let currentTaskId = null;
  let boardSocket = null;
  let activeProjectMembers = [];

  function initBoard() {
    const boardRoot = document.getElementById('boardRoot');
    if (!boardRoot) return;

    const projectId = boardRoot.dataset.projectId;

    initFilters();
    initColumnActions();
    initInlineAddCards();
    initTaskCardsClick();
    initTaskDrawer();
    initWebSocket(projectId);

    // Auto-open task if URL has ?task=ID
    const urlParams = new URLSearchParams(window.location.search);
    const taskIdParam = urlParams.get('task');
    if (taskIdParam) {
      openTaskDrawer(taskIdParam);
    }
  }

  // ==========================================
  // Filtering
  // ==========================================
  function initFilters() {
    const textInput = document.getElementById('boardCardFilterInput');
    const assigneeSelect = document.getElementById('boardAssigneeFilter');
    const prioritySelect = document.getElementById('boardPriorityFilter');
    const labelSelect = document.getElementById('boardLabelFilter');

    function applyFilters() {
      const q = textInput.value.toLowerCase().trim();
      const a = assigneeSelect.value;
      const p = prioritySelect.value;
      const l = labelSelect.value;

      document.querySelectorAll('.task-card').forEach(card => {
        let match = true;

        if (q) {
          const title = card.querySelector('.card-title').textContent.toLowerCase();
          if (!title.includes(q)) match = false;
        }

        if (a && card.dataset.assigneeId !== a) match = false;
        if (p && card.dataset.priority !== p) match = false;
        if (l) {
          const labels = card.dataset.labels ? card.dataset.labels.split(',') : [];
          if (!labels.includes(l)) match = false;
        }

        card.style.display = match ? 'block' : 'none';
      });

      window.FlowboardDragDrop.updateColumnCounts();
    }

    if (textInput) textInput.addEventListener('input', applyFilters);
    if (assigneeSelect) assigneeSelect.addEventListener('change', applyFilters);
    if (prioritySelect) prioritySelect.addEventListener('change', applyFilters);
    if (labelSelect) labelSelect.addEventListener('change', applyFilters);
  }

  // ==========================================
  // Columns CRUD
  // ==========================================
  function initColumnActions() {
    const projectId = document.getElementById('boardRoot').dataset.projectId;

    // Add Column Modal
    const addColModal = document.getElementById('addColumnModal');
    const btnOpenAddCol1 = document.getElementById('btnAddNewColumn');
    const btnOpenAddCol2 = document.getElementById('btnAddNewColumnEnd');
    const btnCancelAddCol = document.getElementById('cancelAddColumnModal');
    const btnCloseAddCol = document.getElementById('closeAddColumnModal');
    const btnSubmitAddCol = document.getElementById('submitAddColumnModal');
    const newColNameInput = document.getElementById('newColNameInput');

    function showAddColModal() {
      newColNameInput.value = '';
      addColModal.classList.add('open');
      setTimeout(() => newColNameInput.focus(), 50);
    }

    if (btnOpenAddCol1) btnOpenAddCol1.addEventListener('click', showAddColModal);
    if (btnOpenAddCol2) btnOpenAddCol2.addEventListener('click', showAddColModal);
    if (btnCancelAddCol) btnCancelAddCol.addEventListener('click', () => addColModal.classList.remove('open'));
    if (btnCloseAddCol) btnCloseAddCol.addEventListener('click', () => addColModal.classList.remove('open'));

    if (btnSubmitAddCol) {
      btnSubmitAddCol.addEventListener('click', async () => {
        const name = newColNameInput.value.trim();
        if (!name) return;
        btnSubmitAddCol.disabled = true;
        try {
          const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/columns/create/`, { name });
          if (res.status === 'ok') {
            addColModal.classList.remove('open');
            window.FlowboardApp.showToast(`Column "${name}" created`);
            // Insert column DOM if not already present
            ensureColumnDOM(res.column);
          }
        } catch (err) {
          window.FlowboardApp.showToast(err.message || 'Error creating column', 'error');
        } finally {
          btnSubmitAddCol.disabled = false;
        }
      });
    }

    // Rename Column Modal
    const renameModal = document.getElementById('renameColumnModal');
    const renameColIdInput = document.getElementById('renameColIdInput');
    const renameColNameInput = document.getElementById('renameColNameInput');
    const btnCloseRename = document.getElementById('closeRenameColumnModal');
    const btnCancelRename = document.getElementById('cancelRenameColumnModal');
    const btnSubmitRename = document.getElementById('submitRenameColumnModal');

    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-rename-col');
      if (btn) {
        const colId = btn.dataset.columnId;
        const currentName = document.getElementById(`colName-${colId}`).textContent;
        renameColIdInput.value = colId;
        renameColNameInput.value = currentName;
        renameModal.classList.add('open');
        setTimeout(() => renameColNameInput.focus(), 50);
      }
    });

    if (btnCloseRename) btnCloseRename.addEventListener('click', () => renameModal.classList.remove('open'));
    if (btnCancelRename) btnCancelRename.addEventListener('click', () => renameModal.classList.remove('open'));

    if (btnSubmitRename) {
      btnSubmitRename.addEventListener('click', async () => {
        const colId = renameColIdInput.value;
        const name = renameColNameInput.value.trim();
        if (!name) return;
        btnSubmitRename.disabled = true;
        try {
          const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/columns/${colId}/rename/`, { name });
          if (res.status === 'ok') {
            renameModal.classList.remove('open');
            const colNameEl = document.getElementById(`colName-${colId}`);
            if (colNameEl) colNameEl.textContent = name;
            window.FlowboardApp.showToast(`Column renamed to "${name}"`);
          }
        } catch (err) {
          window.FlowboardApp.showToast('Failed to rename column', 'error');
        } finally {
          btnSubmitRename.disabled = false;
        }
      });
    }

    // Delete Column
    document.addEventListener('click', async (e) => {
      const btn = e.target.closest('.btn-delete-col');
      if (btn) {
        const colId = btn.dataset.columnId;
        const colName = document.getElementById(`colName-${colId}`).textContent;
        if (!confirm(`Are you sure you want to delete the column "${colName}" and all its cards?`)) {
          return;
        }
        try {
          const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/columns/${colId}/delete/`);
          if (res.status === 'ok') {
            const colEl = document.getElementById(`column-${colId}`);
            if (colEl) colEl.remove();
            window.FlowboardApp.showToast(`Column "${colName}" deleted`);
          }
        } catch (err) {
          window.FlowboardApp.showToast('Failed to delete column', 'error');
        }
      }
    });
  }

  function ensureColumnDOM(col) {
    if (document.getElementById(`column-${col.id}`)) return;

    const canvas = document.getElementById('boardCanvas');
    const endBtn = document.getElementById('btnAddNewColumnEnd');

    const colDiv = document.createElement('div');
    colDiv.className = 'board-column';
    colDiv.dataset.columnId = col.id;
    colDiv.id = `column-${col.id}`;
    colDiv.innerHTML = `
      <div class="column-header">
        <div class="column-header-left">
          <span class="column-name" id="colName-${col.id}">${window.FlowboardApp.escapeHTML(col.name)}</span>
          <span class="column-badge" id="colCount-${col.id}">0</span>
        </div>
        <div style="display: flex; align-items: center; gap: 2px;">
          <button type="button" class="icon-btn btn-sm btn-rename-col" data-column-id="${col.id}" title="Rename column" aria-label="Rename column">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg>
          </button>
          <button type="button" class="icon-btn btn-sm btn-delete-col" data-column-id="${col.id}" title="Delete column" aria-label="Delete column">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
          </button>
        </div>
      </div>
      <div class="column-cards-container" id="cardsContainer-${col.id}"></div>
      <div class="column-footer">
        <div class="add-card-wrapper" id="addCardWrapper-${col.id}">
          <button type="button" class="btn btn-ghost btn-sm btn-show-add-card" data-column-id="${col.id}" style="width: 100%; justify-content: flex-start; color: var(--text-muted);" id="btnTriggerAddCard-${col.id}">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            <span>Add card</span>
          </button>
          <div class="add-card-form" id="addCardForm-${col.id}" style="display: none;">
            <textarea class="form-textarea add-card-textarea" id="addCardText-${col.id}" placeholder="Enter a title for this card..." rows="2" style="font-size: 13px; margin-bottom: 8px;"></textarea>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button type="button" class="btn btn-primary btn-sm btn-submit-add-card" data-column-id="${col.id}" id="btnSubmitAddCard-${col.id}">Add card</button>
              <button type="button" class="btn btn-ghost btn-sm btn-cancel-add-card" data-column-id="${col.id}" id="btnCancelAddCard-${col.id}">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    `;

    canvas.insertBefore(colDiv, endBtn);
  }

  // ==========================================
  // Inline Add Card Form
  // ==========================================
  function initInlineAddCards() {
    const projectId = document.getElementById('boardRoot').dataset.projectId;

    document.addEventListener('click', (e) => {
      const showBtn = e.target.closest('.btn-show-add-card');
      if (showBtn) {
        const colId = showBtn.dataset.columnId;
        const form = document.getElementById(`addCardForm-${colId}`);
        const textarea = document.getElementById(`addCardText-${colId}`);
        showBtn.style.display = 'none';
        form.style.display = 'block';
        textarea.focus();
      }

      const cancelBtn = e.target.closest('.btn-cancel-add-card');
      if (cancelBtn) {
        const colId = cancelBtn.dataset.columnId;
        const showBtn = document.getElementById(`btnTriggerAddCard-${colId}`);
        const form = document.getElementById(`addCardForm-${colId}`);
        const textarea = document.getElementById(`addCardText-${colId}`);
        textarea.value = '';
        form.style.display = 'none';
        showBtn.style.display = 'flex';
      }

      const submitBtn = e.target.closest('.btn-submit-add-card');
      if (submitBtn) {
        const colId = submitBtn.dataset.columnId;
        submitNewCard(projectId, colId);
      }
    });

    // Enter key submit on textarea (shift+enter for newline)
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && e.target.classList.contains('add-card-textarea')) {
        e.preventDefault();
        const colId = e.target.id.replace('addCardText-', '');
        submitNewCard(projectId, colId);
      }
    });
  }

  async function submitNewCard(projectId, colId) {
    const textarea = document.getElementById(`addCardText-${colId}`);
    const title = textarea.value.trim();
    if (!title) return;

    textarea.disabled = true;
    try {
      const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/create/`, {
        title,
        column_id: parseInt(colId, 10),
      });

      if (res.status === 'ok') {
        renderCardInColumn(res.task);
        textarea.value = '';
        textarea.disabled = false;
        textarea.focus();
        window.FlowboardApp.showToast(`Created "${title}"`);
      }
    } catch (err) {
      window.FlowboardApp.showToast('Failed to create task', 'error');
      textarea.disabled = false;
    }
  }

  function renderCardInColumn(task, prepend = false) {
    const existing = document.getElementById(`taskCard-${task.id}`);
    if (existing) existing.remove();

    const container = document.getElementById(`cardsContainer-${task.column_id}`);
    if (!container) return;

    const card = document.createElement('div');
    card.className = 'task-card just-updated';
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.dataset.columnId = task.column_id;
    card.dataset.priority = task.priority;
    card.dataset.assigneeId = task.assignee ? task.assignee.id : '';
    card.dataset.labels = task.labels ? task.labels.map(l => l.id).join(',') : '';
    card.tabIndex = 0;
    card.role = 'button';
    card.setAttribute('aria-label', `Task ${task.title}`);
    card.id = `taskCard-${task.id}`;

    const labelsHTML = task.labels && task.labels.length > 0
      ? task.labels.map(l => `
        <span class="label-chip" style="background-color: ${l.color}20; color: ${l.color}; border: 1px solid ${l.color}40;">
          ${window.FlowboardApp.escapeHTML(l.name)}
        </span>
      `).join('')
      : '';

    const dueDateHTML = task.due_date
      ? `
        <span class="card-due-date" title="Due date: ${task.due_date}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
          <span>${task.due_date_formatted || task.due_date}</span>
        </span>
      `
      : '';

    const commentsHTML = task.comments_count > 0
      ? `
        <span class="card-comment-count" title="${task.comments_count} comments">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          <span>${task.comments_count}</span>
        </span>
      `
      : '';

    const assigneeHTML = task.assignee
      ? `
        <div class="avatar avatar-sm" style="background-color: ${task.assignee.avatar_color || '#2563EB'};" title="Assigned to ${window.FlowboardApp.escapeHTML(task.assignee.display_name)}">
          ${task.assignee.avatar_url ? `<img src="${task.assignee.avatar_url}" alt="${task.assignee.display_name}">` : `<span>${task.assignee.initials}</span>`}
        </div>
      `
      : '';

    card.innerHTML = `
      <div class="card-top-row">
        <div class="card-labels">${labelsHTML}</div>
        <span class="priority-dot ${task.priority}" title="Priority: ${task.priority}"></span>
      </div>
      <div class="card-title">${window.FlowboardApp.escapeHTML(task.title)}</div>
      <div class="card-bottom-row">
        <div class="card-meta-left">
          ${dueDateHTML}
          ${commentsHTML}
        </div>
        ${assigneeHTML}
      </div>
    `;

    if (prepend) {
      container.prepend(card);
    } else {
      container.appendChild(card);
    }

    window.FlowboardDragDrop.updateColumnCounts();
  }

  // ==========================================
  // Task Details Drawer
  // ==========================================
  function initTaskCardsClick() {
    document.addEventListener('click', (e) => {
      const card = e.target.closest('.task-card');
      if (card && !card.classList.contains('is-dragging')) {
        openTaskDrawer(card.dataset.taskId);
      }
    });

    document.addEventListener('keydown', (e) => {
      if ((e.key === 'Enter' || e.key === ' ') && e.target.classList.contains('task-card')) {
        e.preventDefault();
        openTaskDrawer(e.target.dataset.taskId);
      }
    });
  }

  async function openTaskDrawer(taskId) {
    const projectId = document.getElementById('boardRoot').dataset.projectId;
    const drawer = document.getElementById('taskDetailDrawer');
    currentTaskId = taskId;

    drawer.classList.add('open');

    // Update URL query string without reloading page
    const url = new URL(window.location);
    url.searchParams.set('task', taskId);
    window.history.pushState({}, '', url);

    try {
      const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${taskId}/`, null, 'GET');
      if (res.status === 'ok') {
        populateDrawer(res.task, res.comments, res.activities);
      }
    } catch (err) {
      window.FlowboardApp.showToast('Failed to load task details', 'error');
    }
  }

  function populateDrawer(task, comments, activities) {
    document.getElementById('taskDrawerTitleInput').value = task.title;
    document.getElementById('taskDrawerColumnSelect').value = task.column_id;
    document.getElementById('taskDrawerAssigneeSelect').value = task.assignee ? task.assignee.id : '';
    document.getElementById('taskDrawerPrioritySelect').value = task.priority;
    document.getElementById('taskDrawerDueDateInput').value = task.due_date || '';
    document.getElementById('taskDrawerDescInput').value = task.description || '';

    // Labels checkboxes
    const taskLabelIds = task.labels ? task.labels.map(l => l.id.toString()) : [];
    document.querySelectorAll('.task-drawer-label-cb').forEach(cb => {
      cb.checked = taskLabelIds.includes(cb.value);
    });

    // Comments list
    renderCommentsList(comments);

    // Activities list
    renderActivitiesList(activities);
  }

  function renderCommentsList(comments) {
    const container = document.getElementById('taskDrawerCommentsList');
    if (!comments || comments.length === 0) {
      container.innerHTML = '<div style="font-size: 12px; color: var(--text-muted); padding: 8px 0;">No comments yet. Mention teammates with @username.</div>';
      return;
    }

    container.innerHTML = comments.map(c => `
      <div class="comment-item" id="commentItem-${c.id}">
        <div class="avatar avatar-sm" style="background-color: ${c.avatar_color || '#2563EB'};">
          ${c.avatar_url ? `<img src="${c.avatar_url}" alt="${c.display_name}">` : `<span>${c.initials}</span>`}
        </div>
        <div class="comment-content-box">
          <div class="comment-header">
            <span class="comment-author">${window.FlowboardApp.escapeHTML(c.display_name)}</span>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="comment-time">${c.created_at}</span>
              ${c.is_own ? `
                <button type="button" class="icon-btn btn-sm btn-delete-comment" data-comment-id="${c.id}" title="Delete comment" style="width: 18px; height: 18px;">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              ` : ''}
            </div>
          </div>
          <div class="comment-text">${window.FlowboardApp.escapeHTML(c.content)}</div>
        </div>
      </div>
    `).join('');
  }

  function renderActivitiesList(activities) {
    const container = document.getElementById('taskDrawerActivitiesList');
    if (!activities || activities.length === 0) {
      container.innerHTML = '<div style="font-size: 12px; color: var(--text-muted);">No recorded activity.</div>';
      return;
    }

    container.innerHTML = activities.map(a => `
      <div style="display: flex; gap: 6px;">
        <span style="font-weight: 500; color: var(--text-primary);">${window.FlowboardApp.escapeHTML(a.user_name)}</span>
        <span>${window.FlowboardApp.escapeHTML(a.details)}</span>
        <span style="color: var(--text-muted); margin-left: auto;">${a.created_at}</span>
      </div>
    `).join('');
  }

  function initTaskDrawer() {
    const projectId = document.getElementById('boardRoot').dataset.projectId;
    const drawer = document.getElementById('taskDetailDrawer');
    const closeBtn = document.getElementById('btnCloseDrawer');

    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        drawer.classList.remove('open');
        currentTaskId = null;
        const url = new URL(window.location);
        url.searchParams.delete('task');
        window.history.pushState({}, '', url);
      });
    }

    // Auto-save title on change
    const titleInput = document.getElementById('taskDrawerTitleInput');
    titleInput.addEventListener('blur', () => saveTaskField('title', titleInput.value.trim()));
    titleInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        titleInput.blur();
      }
    });

    // Auto-save column change
    document.getElementById('taskDrawerColumnSelect').addEventListener('change', async (e) => {
      const targetColId = parseInt(e.target.value, 10);
      try {
        await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${currentTaskId}/move/`, {
          target_column_id: targetColId,
          new_order: 0,
        });
        const card = document.getElementById(`taskCard-${currentTaskId}`);
        if (card) {
          const targetContainer = document.getElementById(`cardsContainer-${targetColId}`);
          if (targetContainer) targetContainer.prepend(card);
          card.dataset.columnId = targetColId;
          window.FlowboardDragDrop.updateColumnCounts();
        }
      } catch (err) {
        window.FlowboardApp.showToast('Failed to change column', 'error');
      }
    });

    // Auto-save assignee
    document.getElementById('taskDrawerAssigneeSelect').addEventListener('change', (e) => {
      saveTaskField('assignee_id', e.target.value ? parseInt(e.target.value, 10) : null);
    });

    // Auto-save priority
    document.getElementById('taskDrawerPrioritySelect').addEventListener('change', (e) => {
      saveTaskField('priority', e.target.value);
    });

    // Auto-save due date
    document.getElementById('taskDrawerDueDateInput').addEventListener('change', (e) => {
      saveTaskField('due_date', e.target.value || null);
    });

    // Labels checkboxes
    document.querySelectorAll('.task-drawer-label-cb').forEach(cb => {
      cb.addEventListener('change', () => {
        const checked = Array.from(document.querySelectorAll('.task-drawer-label-cb:checked')).map(c => parseInt(c.value, 10));
        saveTaskField('label_ids', checked);
      });
    });

    // Save description button
    document.getElementById('btnSaveTaskDesc').addEventListener('click', async () => {
      const desc = document.getElementById('taskDrawerDescInput').value;
      await saveTaskField('description', desc);
      window.FlowboardApp.showToast('Description saved');
    });

    // Submit new comment
    const commentInput = document.getElementById('taskNewCommentInput');
    const commentSubmitBtn = document.getElementById('btnSubmitNewComment');

    async function submitComment() {
      const content = commentInput.value.trim();
      if (!content || !currentTaskId) return;

      commentSubmitBtn.disabled = true;
      try {
        const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${currentTaskId}/comments/`, {
          content,
        });
        if (res.status === 'ok') {
          commentInput.value = '';
          appendCommentToDrawer(res.comment);
          window.FlowboardApp.showToast('Comment posted');
        }
      } catch (err) {
        window.FlowboardApp.showToast(err.message || 'Failed to post comment', 'error');
      } finally {
        commentSubmitBtn.disabled = false;
      }
    }

    if (commentSubmitBtn) commentSubmitBtn.addEventListener('click', submitComment);
    if (commentInput) {
      commentInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          submitComment();
        }
      });
    }

    // Delete comment
    document.addEventListener('click', async (e) => {
      const delBtn = e.target.closest('.btn-delete-comment');
      if (delBtn) {
        const commentId = delBtn.dataset.commentId;
        if (!confirm('Delete this comment?')) return;
        try {
          const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/comments/${commentId}/delete/`);
          if (res.status === 'ok') {
            const item = document.getElementById(`commentItem-${commentId}`);
            if (item) item.remove();
          }
        } catch (err) {
          window.FlowboardApp.showToast('Failed to delete comment', 'error');
        }
      }
    });

    // Delete task button
    const deleteTaskBtn = document.getElementById('btnDeleteTaskInDrawer');
    if (deleteTaskBtn) {
      deleteTaskBtn.addEventListener('click', async () => {
        if (!confirm('Are you sure you want to delete this task?')) return;
        deleteTaskBtn.disabled = true;
        try {
          const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${currentTaskId}/delete/`);
          if (res.status === 'ok') {
            const card = document.getElementById(`taskCard-${currentTaskId}`);
            if (card) card.remove();
            drawer.classList.remove('open');
            currentTaskId = null;
            window.FlowboardDragDrop.updateColumnCounts();
            window.FlowboardApp.showToast('Task deleted');
          }
        } catch (err) {
          window.FlowboardApp.showToast('Failed to delete task', 'error');
        } finally {
          deleteTaskBtn.disabled = false;
        }
      });
    }
  }

  async function saveTaskField(fieldName, value) {
    if (!currentTaskId) return;
    const projectId = document.getElementById('boardRoot').dataset.projectId;
    const payload = {};
    payload[fieldName] = value;

    try {
      const res = await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${currentTaskId}/update/`, payload);
      if (res.status === 'ok') {
        renderCardInColumn(res.task);
      }
    } catch (err) {
      window.FlowboardApp.showToast(`Failed to update ${fieldName}`, 'error');
    }
  }

  function appendCommentToDrawer(comment) {
    const list = document.getElementById('taskDrawerCommentsList');
    if (!list) return;

    if (list.querySelector('.comment-item') === null) {
      list.innerHTML = '';
    }

    const item = document.createElement('div');
    item.className = 'comment-item';
    item.id = `commentItem-${comment.id}`;
    item.innerHTML = `
      <div class="avatar avatar-sm" style="background-color: ${comment.avatar_color || '#2563EB'};">
        ${comment.avatar_url ? `<img src="${comment.avatar_url}" alt="${comment.display_name}">` : `<span>${comment.initials}</span>`}
      </div>
      <div class="comment-content-box">
        <div class="comment-header">
          <span class="comment-author">${window.FlowboardApp.escapeHTML(comment.display_name)}</span>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="comment-time">${comment.created_at}</span>
            ${comment.is_own ? `
              <button type="button" class="icon-btn btn-sm btn-delete-comment" data-comment-id="${comment.id}" title="Delete comment" style="width: 18px; height: 18px;">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            ` : ''}
          </div>
        </div>
        <div class="comment-text">${window.FlowboardApp.escapeHTML(comment.content)}</div>
      </div>
    `;

    list.appendChild(item);
  }

  // ==========================================
  // Real-time WebSocket Handler
  // ==========================================
  function initWebSocket(projectId) {
    boardSocket = new window.FlowboardSocket(
      `/ws/board/${projectId}/`,
      (data) => {
        if (data.type === 'presence_update') {
          updatePresenceUI(data.users);
        } else if (data.type === 'board_event') {
          handleBoardEvent(data.event, data.data, data.actor_id);
        }
      }
    );
  }

  function updatePresenceUI(users) {
    const cluster = document.getElementById('presenceCluster');
    if (!cluster) return;

    cluster.innerHTML = users.map(u => `
      <div class="avatar avatar-sm presence-avatar" style="background-color: ${u.avatar_color || '#2563EB'};" title="${window.FlowboardApp.escapeHTML(u.display_name)} is active on this board">
        ${u.avatar_url ? `<img src="${u.avatar_url}" alt="${u.display_name}">` : `<span>${u.initials}</span>`}
      </div>
    `).join('');
  }

  function handleBoardEvent(event, data, actorId) {
    if (event === 'task_created') {
      renderCardInColumn(data.task);
    } else if (event === 'task_updated') {
      renderCardInColumn(data.task);
      if (currentTaskId && currentTaskId === data.task.id.toString()) {
        // Update drawer fields if user has this task open
        document.getElementById('taskDrawerTitleInput').value = data.task.title;
      }
    } else if (event === 'task_moved') {
      const card = document.getElementById(`taskCard-${data.task_id}`);
      const targetContainer = document.getElementById(`cardsContainer-${data.target_column_id}`);
      if (card && targetContainer) {
        const cards = Array.from(targetContainer.querySelectorAll('.task-card'));
        if (data.new_order >= cards.length) {
          targetContainer.appendChild(card);
        } else {
          targetContainer.insertBefore(card, cards[data.new_order]);
        }
        card.dataset.columnId = data.target_column_id;
        card.classList.add('just-updated');
        setTimeout(() => card.classList.remove('just-updated'), 1500);
        window.FlowboardDragDrop.updateColumnCounts();
      }
    } else if (event === 'task_deleted') {
      const card = document.getElementById(`taskCard-${data.task_id}`);
      if (card) card.remove();
      if (currentTaskId && currentTaskId === data.task_id.toString()) {
        document.getElementById('taskDetailDrawer').classList.remove('open');
        currentTaskId = null;
      }
      window.FlowboardDragDrop.updateColumnCounts();
    } else if (event === 'comment_added') {
      if (currentTaskId && currentTaskId === data.task_id.toString()) {
        appendCommentToDrawer(data.comment);
      }
      // Update comment badge on card
      const card = document.getElementById(`taskCard-${data.task_id}`);
      if (card && data.comments_count) {
        let countEl = card.querySelector('.card-comment-count span');
        if (countEl) countEl.textContent = data.comments_count;
      }
    } else if (event === 'column_created') {
      ensureColumnDOM(data.column);
    } else if (event === 'column_renamed') {
      const titleEl = document.getElementById(`colName-${data.column_id}`);
      if (titleEl) titleEl.textContent = data.name;
    } else if (event === 'column_deleted') {
      const colEl = document.getElementById(`column-${data.column_id}`);
      if (colEl) colEl.remove();
    }
  }

  document.addEventListener('DOMContentLoaded', initBoard);
})();
