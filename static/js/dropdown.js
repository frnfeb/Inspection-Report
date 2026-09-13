/* ==========================================================================
   dropdown.js — searchable select component
   Markup contract: see pages/report-form.html for full example.
   Dispatches a bubbling 'select:change' CustomEvent { name, value, label }
   on the `.select` root whenever the value changes (including custom text).
   ========================================================================== */

(function () {
  'use strict';

  function closeAllSelects(except) {
    document.querySelectorAll('.select.is-open').forEach(function (el) {
      if (el !== except) el.classList.remove('is-open');
    });
  }

  function filterOptions(select, query) {
    const q = query.trim().toLowerCase();
    const options = select.querySelectorAll('.select__option:not(.is-custom)');
    let visibleCount = 0;

    options.forEach(function (opt) {
      const match = opt.textContent.toLowerCase().indexOf(q) !== -1;
      opt.classList.toggle('is-hidden-option', !match);
      opt.style.display = match ? '' : 'none';
      if (match) visibleCount++;
    });

    const emptyState = select.querySelector('[data-select-empty]');
    if (emptyState) emptyState.style.display = visibleCount === 0 ? 'block' : 'none';
  }

  function setValue(select, value, label) {
    const valueEl = select.querySelector('[data-select-value]');
    const hiddenInput = select.querySelector('[data-select-hidden-input]');
    const customWrap = select.querySelector('.select__custom-input');
    const customInput = select.querySelector('[data-select-custom-input]');

    select.querySelectorAll('.select__option').forEach(function (opt) {
      opt.classList.toggle('is-selected', opt.dataset.value === value);
    });

    if (value === '__custom__') {
      customWrap.hidden = false;
      window.requestAnimationFrame(function () { customInput.focus(); });
      const customVal = customInput.value.trim();
      valueEl.textContent = customVal || 'Isi nilai custom…';
      valueEl.classList.toggle('is-placeholder', !customVal);
      if (hiddenInput) hiddenInput.value = customVal;
      select.dataset.currentValue = customVal ? '__custom__' : '';
    } else {
      customWrap.hidden = true;
      valueEl.textContent = label;
      valueEl.classList.remove('is-placeholder');
      if (hiddenInput) hiddenInput.value = value;
      select.dataset.currentValue = value;
    }

    select.dispatchEvent(new CustomEvent('select:change', {
      bubbles: true,
      detail: {
        name: select.dataset.name,
        value: hiddenInput ? hiddenInput.value : value,
        label: valueEl.textContent
      }
    }));
  }

  function initSelect(select) {
    if (select.dataset.selectInit) return;
    select.dataset.selectInit = '1';

    const control = select.querySelector('.select__control');
    const searchInput = select.querySelector('[data-select-search]');
    const list = select.querySelector('[data-select-list]');
    const customInput = select.querySelector('[data-select-custom-input]');

    control.addEventListener('click', function () {
      const willOpen = !select.classList.contains('is-open');
      closeAllSelects(select);
      select.classList.toggle('is-open', willOpen);
      if (willOpen && searchInput) {
        window.requestAnimationFrame(function () { searchInput.focus(); });
      }
    });

    if (searchInput) {
      searchInput.addEventListener('input', function () {
        filterOptions(select, searchInput.value);
      });
      searchInput.addEventListener('click', function (e) { e.stopPropagation(); });
    }

    list.addEventListener('click', function (e) {
      const opt = e.target.closest('.select__option');
      if (!opt) return;
      setValue(select, opt.dataset.value, opt.textContent.trim());
      if (opt.dataset.value !== '__custom__') {
        select.classList.remove('is-open');
      }
    });

    if (customInput) {
      customInput.addEventListener('input', function () {
        setValue(select, '__custom__', customInput.value.trim());
      });
      customInput.addEventListener('click', function (e) { e.stopPropagation(); });
      customInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          select.classList.remove('is-open');
        }
      });
    }

    select.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') select.classList.remove('is-open');
    });
  }

  document.addEventListener('click', function (e) {
    const clickedSelect = e.target.closest('.select');
    closeAllSelects(clickedSelect);
  });

  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-select]').forEach(initSelect);
  });

  window.MRG = window.MRG || {};
  window.MRG.initSelect = initSelect;
})();
