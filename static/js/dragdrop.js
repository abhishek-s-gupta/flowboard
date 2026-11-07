/**
 * Flowboard Drag and Drop Engine
 * Smooth HTML5 drag & drop with responsive placeholders, transitions, and keyboard accessibility.
 */

(function () {
  'use strict';

  let draggedCard = null;
  let sourceColumn = null;
  let dropPlaceholder = null;

  function initDragAndDrop() {
    const boardCanvas = document.getElementById('boardCanvas');
    if (!boardCanvas) return;

    // Create persistent placeholder
    dropPlaceholder = document.createElement('div');
    dropPlaceholder.className = 'card-drop-placeholder';

    // Delegate drag events on cards
    document.addEventListener('dragstart', handleDragStart);
    document.addEventListener('dragend', handleDragEnd);
    document.addEventListener('dragover', handleDragOver);
    document.addEventListener('dragenter', handleDragEnter);
    document.addEventListener('dragleave', handleDragLeave);
    document.addEventListener('drop', handleDrop);

    // Keyboard navigation for cards
    document.addEventListener('keydown', handleKeyboardCardMove);
  }

  function handleDragStart(e) {
    const card = e.target.closest('.task-card');
    if (!card) return;

    draggedCard = card;
    sourceColumn = card.closest('.board-column');

    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', card.dataset.taskId);

    // Delay class addition so dragged ghost maintains original styling
    setTimeout(() => {
      card.classList.add('is-dragging');
    }, 0);
  }

  function handleDragOver(e) {
    if (!draggedCard) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';

    const column = e.target.closest('.board-column');
    if (!column) return;

    const cardsContainer = column.querySelector('.column-cards-container');
    if (!cardsContainer) return;

    const afterElement = getDragAfterElement(cardsContainer, e.clientY);
    if (!afterElement) {
      cardsContainer.appendChild(dropPlaceholder);
    } else {
      cardsContainer.insertBefore(dropPlaceholder, afterElement);
    }
  }

  function handleDragEnter(e) {
    if (!draggedCard) return;
    const column = e.target.closest('.board-column');
    if (column) {
      e.preventDefault();
    }
  }

  function handleDragLeave(e) {
    // Handled by dragover repositioning
  }

  async function handleDrop(e) {
    if (!draggedCard) return;
    e.preventDefault();

    const targetColumn = e.target.closest('.board-column');
    if (!targetColumn) {
      cleanupDrag();
      return;
    }

    const cardsContainer = targetColumn.querySelector('.column-cards-container');
    const targetColumnId = targetColumn.dataset.columnId;
    const taskId = draggedCard.dataset.taskId;

    // Insert card into position of placeholder
    if (dropPlaceholder.parentElement === cardsContainer) {
      cardsContainer.insertBefore(draggedCard, dropPlaceholder);
    } else {
      cardsContainer.appendChild(draggedCard);
    }

    // Calculate new index in target container
    const cards = Array.from(cardsContainer.querySelectorAll('.task-card'));
    const newOrder = cards.indexOf(draggedCard);

    // Update dataset on card
    draggedCard.dataset.columnId = targetColumnId;

    // Update column count badges
    updateColumnCounts();

    // Call backend API
    const projectId = document.getElementById('boardRoot').dataset.projectId;
    try {
      await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${taskId}/move/`, {
        target_column_id: parseInt(targetColumnId, 10),
        new_order: newOrder,
      });
    } catch (err) {
      window.FlowboardApp.showToast('Failed to save card position', 'error');
    }

    cleanupDrag();
  }

  function handleDragEnd(e) {
    cleanupDrag();
  }

  function cleanupDrag() {
    if (draggedCard) {
      draggedCard.classList.remove('is-dragging');
      draggedCard = null;
    }
    if (dropPlaceholder && dropPlaceholder.parentElement) {
      dropPlaceholder.remove();
    }
    sourceColumn = null;
  }

  function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.task-card:not(.is-dragging)')];

    return draggableElements.reduce((closest, child) => {
      const box = child.getBoundingClientRect();
      const offset = y - box.top - box.height / 2;
      if (offset < 0 && offset > closest.offset) {
        return { offset: offset, element: child };
      } else {
        return closest;
      }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
  }

  function updateColumnCounts() {
    document.querySelectorAll('.board-column').forEach(col => {
      const colId = col.dataset.columnId;
      const count = col.querySelectorAll('.task-card:not([style*="display: none"])').length;
      const badge = document.getElementById(`colCount-${colId}`);
      if (badge) badge.textContent = count;
    });
  }

  // Keyboard accessibility: Alt + Arrow keys to move focused card
  async function handleKeyboardCardMove(e) {
    const focusedCard = document.activeElement ? document.activeElement.closest('.task-card') : null;
    if (!focusedCard) return;

    if (!e.altKey && !e.ctrlKey) return;

    const currentColumn = focusedCard.closest('.board-column');
    if (!currentColumn) return;

    const currentContainer = currentColumn.querySelector('.column-cards-container');
    const allColumns = Array.from(document.querySelectorAll('.board-column'));
    const currentColIndex = allColumns.indexOf(currentColumn);
    const taskId = focusedCard.dataset.taskId;
    const projectId = document.getElementById('boardRoot').dataset.projectId;

    let targetColumn = currentColumn;
    let newOrder = 0;

    if (e.key === 'ArrowRight' && currentColIndex < allColumns.length - 1) {
      e.preventDefault();
      targetColumn = allColumns[currentColIndex + 1];
      const targetContainer = targetColumn.querySelector('.column-cards-container');
      targetContainer.appendChild(focusedCard);
      newOrder = targetContainer.querySelectorAll('.task-card').length - 1;
    } else if (e.key === 'ArrowLeft' && currentColIndex > 0) {
      e.preventDefault();
      targetColumn = allColumns[currentColIndex - 1];
      const targetContainer = targetColumn.querySelector('.column-cards-container');
      targetContainer.appendChild(focusedCard);
      newOrder = targetContainer.querySelectorAll('.task-card').length - 1;
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextCard = focusedCard.nextElementSibling;
      if (nextCard && nextCard.classList.contains('task-card')) {
        currentContainer.insertBefore(nextCard, focusedCard);
        newOrder = Array.from(currentContainer.querySelectorAll('.task-card')).indexOf(focusedCard);
      } else {
        return;
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const prevCard = focusedCard.previousElementSibling;
      if (prevCard && prevCard.classList.contains('task-card')) {
        currentContainer.insertBefore(focusedCard, prevCard);
        newOrder = Array.from(currentContainer.querySelectorAll('.task-card')).indexOf(focusedCard);
      } else {
        return;
      }
    } else {
      return;
    }

    focusedCard.dataset.columnId = targetColumn.dataset.columnId;
    focusedCard.focus();
    updateColumnCounts();

    try {
      await window.FlowboardApp.fetchJSON(`/projects/api/${projectId}/tasks/${taskId}/move/`, {
        target_column_id: parseInt(targetColumn.dataset.columnId, 10),
        new_order: newOrder,
      });
      window.FlowboardApp.showToast('Card moved');
    } catch (err) {
      window.FlowboardApp.showToast('Failed to move card', 'error');
    }
  }

  window.FlowboardDragDrop = {
    init: initDragAndDrop,
    updateColumnCounts,
  };

  document.addEventListener('DOMContentLoaded', initDragAndDrop);
})();
