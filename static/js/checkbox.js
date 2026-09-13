/* ==========================================================================
   checkbox.js — card-checkboxes, inspection search, accordion, toggle/radio
   ========================================================================== */

(function () {
  'use strict';

  /* ---------------- Card checkbox (Inspection step) ---------------- */
  function initCardChecks() {
    document.addEventListener('click', function (e) {
      const card = e.target.closest('.card-check');
      if (!card) return;
      card.classList.toggle('is-selected');
      updateGroupCount(card.closest('.inspection-group'));
      document.dispatchEvent(new CustomEvent('inspection:change'));
    });
  }

  function updateGroupCount(group) {
    if (!group) return;
    const counter = group.querySelector('[data-group-count]');
    if (!counter) return;
    const selected = group.querySelectorAll('.card-check.is-selected').length;
    counter.textContent = selected + ' dipilih';
  }

  /* ---------------- Inspection search ---------------- */
  function initInspectionSearch() {
    const input = document.querySelector('[data-inspection-search]');
    if (!input) return;
    input.addEventListener('input', function () {
      const q = input.value.trim().toLowerCase();
      document.querySelectorAll('.card-check').forEach(function (card) {
        const match = card.textContent.toLowerCase().indexOf(q) !== -1;
        card.classList.toggle('is-hidden', !match);
      });
    });
  }

  /* ---------------- Accordion (CPL Pump) ---------------- */
  function updateAccordionProgress(item) {
    const badge = item.querySelector('[data-accordion-progress]');
    if (!badge) return;
    const total = item.querySelectorAll('.card-check').length;
    const selected = item.querySelectorAll('.card-check.is-selected').length;
    badge.textContent = selected + ' / ' + total + ' item';
    badge.classList.toggle('has-items', selected > 0);
  }

  function initAccordion() {
    document.querySelectorAll('.accordion-item').forEach(function (item) {
      updateAccordionProgress(item);
      const head = item.querySelector('.accordion-item__head');
      if (head) {
        head.addEventListener('click', function () {
          item.classList.toggle('is-open');
        });
      }
    });

    document.addEventListener('click', function (e) {
      if (e.target.closest('.card-check')) {
        const item = e.target.closest('.accordion-item');
        if (item) updateAccordionProgress(item);
        document.dispatchEvent(new CustomEvent('cplpump:change'));
      }
    });
  }

  function initAccordionSearch() {
    const input = document.querySelector('[data-accordion-search]');
    if (!input) return;
    input.addEventListener('input', function () {
      const q = input.value.trim().toLowerCase();
      document.querySelectorAll('.accordion-item').forEach(function (item) {
        const title = item.querySelector('.accordion-item__title').textContent.toLowerCase();
        const match = title.indexOf(q) !== -1;
        item.classList.toggle('is-hidden', !match);
        if (match && q) item.classList.add('is-open');
      });
    });
  }

  /* ---------------- Toggle-check (Generate step: sheets / outputs) ---------------- */
  function initToggleChecks() {
    document.addEventListener('click', function (e) {
      const toggle = e.target.closest('.toggle-check');
      if (!toggle) return;
      toggle.classList.toggle('is-checked');
      document.dispatchEvent(new CustomEvent('generate-options:change'));
    });
  }

  /* ---------------- Radio row (Generate step: paper size) ---------------- */
  function initRadioRows() {
    document.addEventListener('click', function (e) {
      const row = e.target.closest('.radio-row');
      if (!row) return;
      const group = row.closest('[data-radio-group]');
      if (group) {
        group.querySelectorAll('.radio-row').forEach(function (r) { r.classList.remove('is-checked'); });
      }
      row.classList.add('is-checked');
      document.dispatchEvent(new CustomEvent('generate-options:change'));
    });
  }

  /* ---------------- Segmented control (e.g. Shift) ---------------- */
  function initSegmented() {
    document.addEventListener('click', function (e) {
      const opt = e.target.closest('.segmented__opt');
      if (!opt) return;
      const group = opt.closest('.segmented');
      group.querySelectorAll('.segmented__opt').forEach(function (o) { o.classList.remove('is-active'); });
      opt.classList.add('is-active');
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initCardChecks();
    initInspectionSearch();
    initAccordion();
    initAccordionSearch();
    initToggleChecks();
    initRadioRows();
    initSegmented();
  });

  window.MRG = window.MRG || {};
  window.MRG.updateGroupCount = updateGroupCount;
})();
