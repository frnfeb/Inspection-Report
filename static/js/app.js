/* ==========================================================================
   app.js — shared shell behaviour used on every page
   (sidebar collapse/drawer, ripple buttons, toast notifications)
   ========================================================================== */

(function () {
  'use strict';

  /* ---------------- Icons ---------------- */
  function initIcons() {
    if (window.lucide) window.lucide.createIcons();
  }

  /* ---------------- Sidebar ---------------- */
  function initSidebar() {
    const collapseBtn = document.querySelector('[data-sidebar-collapse]');
    const menuBtn = document.querySelector('[data-sidebar-open]');
    const backdrop = document.querySelector('[data-sidebar-backdrop]');
    const body = document.body;

    if (collapseBtn) {
      // restore preference
      if (localStorage.getItem('mrg.sidebarCollapsed') === '1') {
        body.classList.add('sidebar-collapsed');
      }
      collapseBtn.addEventListener('click', function () {
        body.classList.toggle('sidebar-collapsed');
        localStorage.setItem('mrg.sidebarCollapsed', body.classList.contains('sidebar-collapsed') ? '1' : '0');
      });
    }

    if (menuBtn) {
      menuBtn.addEventListener('click', function () {
        body.classList.add('sidebar-open');
      });
    }

    if (backdrop) {
      backdrop.addEventListener('click', function () {
        body.classList.remove('sidebar-open');
      });
    }

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') body.classList.remove('sidebar-open');
    });
  }

  /* ---------------- Ripple buttons ---------------- */
  function initRipple() {
    document.addEventListener('click', function (e) {
      const btn = e.target.closest('.btn');
      if (!btn) return;

      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';

      btn.appendChild(ripple);
      window.setTimeout(function () { ripple.remove(); }, 620);
    });
  }

  /* ---------------- Toast notifications ---------------- */
  const TOAST_ICONS = {
    success: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>',
    error: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    info: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="11"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>'
  };

  function getToastStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }

  function showToast(opts) {
    const options = typeof opts === 'string' ? { message: opts } : (opts || {});
    const type = options.type || 'info';
    const title = options.title || ({ success: 'Berhasil', error: 'Terjadi kesalahan', info: 'Informasi' })[type];
    const message = options.message || '';
    const duration = options.duration || 4200;

    const stack = getToastStack();
    const toast = document.createElement('div');
    toast.className = 'toast toast--' + type;
    toast.innerHTML =
      '<span class="toast__icon">' + TOAST_ICONS[type] + '</span>' +
      '<div class="toast__body"><strong>' + title + '</strong><span>' + message + '</span></div>' +
      '<button class="toast__close" aria-label="Tutup notifikasi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>';

    stack.appendChild(toast);

    function remove() {
      toast.classList.add('is-leaving');
      window.setTimeout(function () { toast.remove(); }, 220);
    }

    toast.querySelector('.toast__close').addEventListener('click', remove);
    window.setTimeout(remove, duration);
  }

  /* ---------------- Loading overlay ---------------- */
  function setLoading(visible, message) {
    let overlay = document.querySelector('.loading-overlay');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.innerHTML =
        '<div class="loading-card">' +
        '  <div class="loading-rings"><span></span><span></span></div>' +
        '  <p data-loading-text>Memproses…</p>' +
        '</div>';
      document.body.appendChild(overlay);
    }
    if (message) overlay.querySelector('[data-loading-text]').textContent = message;
    overlay.classList.toggle('is-visible', !!visible);
  }

  window.MRG = window.MRG || {};
  window.MRG.toast = showToast;
  window.MRG.setLoading = setLoading;

  document.addEventListener('DOMContentLoaded', function () {
    initIcons();
    initSidebar();
    initRipple();
  });
})();
