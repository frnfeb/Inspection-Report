/* ==========================================================================
   upload.js — drag & drop photo upload with preview + delete
   Markup contract: <div class="upload-section" data-upload-zone="before"> …
   ========================================================================== */

(function () {
  'use strict';

  const MAX_SIZE = 10 * 1024 * 1024; // 10MB
  const removeIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';

  function updateCount(section) {
    const grid = section.querySelector('[data-upload-grid]');
    const countEl = section.querySelector('[data-upload-count]');
    const count = grid.children.length;
    if (countEl) countEl.textContent = count + (count === 1 ? ' foto' : ' foto');
    document.dispatchEvent(new CustomEvent('upload:change', {
      detail: { zone: section.dataset.uploadZone, count: count }
    }));
  }

  function addThumb(section, file) {
    if (!file.type.startsWith('image/')) {
      window.MRG && window.MRG.toast({ type: 'error', title: 'File tidak didukung', message: file.name + ' bukan file gambar.' });
      return;
    }
    if (file.size > MAX_SIZE) {
      window.MRG && window.MRG.toast({ type: 'error', title: 'File terlalu besar', message: file.name + ' melebihi 10MB.' });
      return;
    }

    const grid = section.querySelector('[data-upload-grid]');
    const reader = new FileReader();
    reader.onload = function (e) {
      const thumb = document.createElement('div');
      thumb.className = 'upload-thumb';
      thumb.innerHTML =
        '<img src="' + e.target.result + '" alt="' + file.name + '">' +
        '<button type="button" class="upload-thumb__remove" aria-label="Hapus foto">' + removeIcon + '</button>' +
        '<span class="upload-thumb__name">' + file.name + '</span>';
      thumb.dataset.src = e.target.result;
      grid.appendChild(thumb);
      updateCount(section);
    };
    reader.readAsDataURL(file);
  }

  function handleFiles(section, fileList) {
    Array.from(fileList).forEach(function (file) { addThumb(section, file); });
  }

  function initZone(section) {
    const dropzone = section.querySelector('[data-dropzone]');
    const input = section.querySelector('[data-upload-input]');
    const grid = section.querySelector('[data-upload-grid]');

    dropzone.addEventListener('click', function () { input.click(); });
    dropzone.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
    });

    input.addEventListener('change', function () {
      handleFiles(section, input.files);
      input.value = '';
    });

    ['dragenter', 'dragover'].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add('is-dragover');
      });
    });

    ['dragleave', 'drop'].forEach(function (evt) {
      dropzone.addEventListener(evt, function (e) {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove('is-dragover');
      });
    });

    dropzone.addEventListener('drop', function (e) {
      if (e.dataTransfer && e.dataTransfer.files.length) {
        handleFiles(section, e.dataTransfer.files);
      }
    });

    grid.addEventListener('click', function (e) {
      const removeBtn = e.target.closest('.upload-thumb__remove');
      if (!removeBtn) return;
      removeBtn.closest('.upload-thumb').remove();
      updateCount(section);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-upload-zone]').forEach(initZone);
  });
})();
