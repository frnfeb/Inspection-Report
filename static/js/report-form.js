/* ==========================================================================
   report-form.js — repeating rows, cause checkboxes, section scroll-spy
   for the single-page ISI DATA / AUTO DARI ISI DATA form.
   ========================================================================== */

(function () {
  'use strict';

  /* ---------------- Cause checkboxes ---------------- */
  function initCauseChecks() {
    document.addEventListener('click', function (e) {
      const item = e.target.closest('.check-item');
      if (!item) return;
      item.classList.toggle('is-checked');
    });
  }

  /* ---------------- Repeating rows (PHENOMENA / CONTENT / PARTS) ---------------- */
  function renumberRows(block) {
    Array.from(block.querySelectorAll('.repeat-row')).forEach(function (row, idx) {
      row.querySelector('.repeat-row__num').textContent = idx + 1;
    });
  }

  function updateAddState(wrapper) {
    const block = wrapper.querySelector('.repeat-block');
    const addBtn = wrapper.querySelector('[data-repeat-add]');
    const note = wrapper.querySelector('[data-repeat-note]');
    const max = Number(wrapper.dataset.maxRows);
    const count = block.querySelectorAll('.repeat-row').length;
    if (addBtn) addBtn.disabled = count >= max;
    if (note) note.textContent = count + ' / ' + max + ' baris terisi';
  }

  function initRepeatingBlocks() {
    document.querySelectorAll('[data-repeat-wrapper]').forEach(function (wrapper) {
      const block = wrapper.querySelector('.repeat-block');
      const addBtn = wrapper.querySelector('[data-repeat-add]');
      const template = wrapper.querySelector('template').innerHTML;
      const max = Number(wrapper.dataset.maxRows);
      const isTable = block.tagName === 'TBODY';

      addBtn.addEventListener('click', function () {
        if (block.querySelectorAll('.repeat-row').length >= max) return;
        const row = document.createElement(isTable ? 'tr' : 'div');
        row.className = 'repeat-row';
        row.innerHTML = template;
        block.appendChild(row);
        renumberRows(block);
        updateAddState(wrapper);
        if (window.MRG && window.MRG.initSelect) {
          row.querySelectorAll('[data-select]').forEach(window.MRG.initSelect);
        }
      });

      block.addEventListener('click', function (e) {
        const removeBtn = e.target.closest('.repeat-row__remove');
        if (!removeBtn) return;
        if (block.querySelectorAll('.repeat-row').length <= 1) return; // keep at least 1
        removeBtn.closest('.repeat-row').remove();
        renumberRows(block);
        updateAddState(wrapper);
      });

      updateAddState(wrapper);
    });
  }

  /* ---------------- Scroll-spy for doc-toc ---------------- */
  function initScrollSpy() {
    const links = Array.from(document.querySelectorAll('.doc-toc a'));
    const sections = links
      .map(function (l) { return document.querySelector(l.getAttribute('href')); })
      .filter(Boolean);
    if (!sections.length) return;

    function onScroll() {
      let activeIdx = 0;
      const scrollPos = window.scrollY + 140;
      sections.forEach(function (sec, idx) {
        if (sec.offsetTop <= scrollPos) activeIdx = idx;
      });
      links.forEach(function (l, idx) { l.classList.toggle('is-active', idx === activeIdx); });
    }
    document.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------------- CPL Pump unit select (Custom reveal) ---------------- */
  function initUnitSelects() {
    document.addEventListener('change', function (e) {
      const select = e.target.closest('[data-unit-select]');
      if (!select) return;
      const customInput = select.parentElement.querySelector('.unit-custom-input');
      if (!customInput) return;
      const isCustom = select.value === '__custom__';
      customInput.hidden = !isCustom;
      if (isCustom) customInput.focus();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initCauseChecks();
    initRepeatingBlocks();
    initScrollSpy();
    initUnitSelects();
  });
})();
