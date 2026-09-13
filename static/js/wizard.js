/* ==========================================================================
   wizard.js — step navigation, progress rail, validation gate, filename preview
   ========================================================================== */

(function () {
  'use strict';

  const STEP_COUNT = 5;
  const STEP_TITLES = ['General Information', 'Inspection', 'CPL Pump', 'Photo', 'Generate'];
  let current = 0;
  let maxReached = 0;

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $all(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

  function sanitizeFilenamePart(str) {
    if (!str) return '';
    return str
      .trim()
      .replace(/[\\/:*?"<>|]/g, '_')
      .replace(/\s+/g, '_')
      .replace(/_+/g, '_')
      .replace(/^_|_$/g, '');
  }

  function getFieldValue(name) {
    const el = document.querySelector('[name="' + name + '"]');
    if (!el) return '';
    return (el.value || '').trim();
  }

  function updateFilenamePreview() {
    const chip = $('[data-filename-chip]');
    if (!chip) return;

    const tagNo = getFieldValue('tagNumber') || 'TagNo';
    const repairFinish = getFieldValue('repairFinish');
    const problemTitle = getFieldValue('problemTitle') || 'ProblemTitle';
    const nama = getFieldValue('nama') || 'Nama';

    let year = 'YYYY', month = 'MM', day = 'DD';
    if (repairFinish) {
      const d = new Date(repairFinish);
      if (!isNaN(d.getTime())) {
        year = d.getFullYear();
        month = String(d.getMonth() + 1).padStart(2, '0');
        day = String(d.getDate()).padStart(2, '0');
      }
    }

    const parts = [
      sanitizeFilenamePart(tagNo),
      year, month, day,
      sanitizeFilenamePart(problemTitle),
      sanitizeFilenamePart(nama)
    ].filter(Boolean);

    const base = parts.join('_');
    const xlsxOn = $('[data-output-xlsx]') ? $('[data-output-xlsx]').classList.contains('is-checked') : true;
    const pdfOn = $('[data-output-pdf]') ? $('[data-output-pdf]').classList.contains('is-checked') : true;

    let html = '<span>' + base + '</span>';
    const exts = [];
    if (xlsxOn) exts.push('<span class="ext-xlsx">.xlsx</span>');
    if (pdfOn) exts.push('<span class="ext-pdf">.pdf</span>');

    chip.innerHTML = html;
    const extWrap = $('[data-filename-exts]');
    if (extWrap) extWrap.innerHTML = exts.join(' &nbsp;&middot;&nbsp; ') || '<span class="ext-pdf">Pilih minimal satu output</span>';
  }

  /* ---------------- Step rail / progress ---------------- */
  function renderRail() {
    $all('.step-rail__item').forEach(function (item, idx) {
      item.classList.toggle('is-active', idx === current);
      item.classList.toggle('is-complete', idx < current);
    });

    const fill = $('.progress-track__fill');
    if (fill) fill.style.width = (((current + 1) / STEP_COUNT) * 100) + '%';

    const metaCurrent = $('[data-progress-current]');
    const metaLabel = $('[data-progress-label]');
    if (metaCurrent) metaCurrent.textContent = 'Step ' + (current + 1) + ' dari ' + STEP_COUNT;
    if (metaLabel) metaLabel.textContent = STEP_TITLES[current];
  }

  function renderPanels() {
    $all('.form-step').forEach(function (panel) {
      panel.classList.toggle('is-active', Number(panel.dataset.stepPanel) === current);
    });

    const backBtn = $('[data-wizard-back]');
    const nextBtn = $('[data-wizard-next]');
    if (backBtn) backBtn.style.visibility = current === 0 ? 'hidden' : 'visible';
    if (nextBtn) {
      nextBtn.innerHTML = current === STEP_COUNT - 1
        ? 'Selesai <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>'
        : 'Lanjut <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>';
      if (window.lucide) { /* icons here are raw svg, no lucide re-init needed */ }
    }

    if (current === STEP_COUNT - 1) updateFilenamePreview();

    document.dispatchEvent(new CustomEvent('wizard:stepchange', { detail: { step: current } }));

    // scroll form panel into view on mobile
    const panelEl = $('.form-panel');
    if (panelEl && window.innerWidth <= 760) {
      panelEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function validateStep(stepIndex) {
    if (stepIndex !== 0) return true; // only General Information has required fields in this prototype
    const requiredFields = $all('[data-step-panel="0"] [required]');
    let firstInvalid = null;
    let valid = true;

    requiredFields.forEach(function (field) {
      const filled = (field.value || '').trim().length > 0;
      const wrapper = field.closest('.field') || field.closest('.select');
      if (!filled) {
        valid = false;
        if (wrapper) wrapper.classList.add('has-error');
        if (!firstInvalid) firstInvalid = field;
      } else if (wrapper) {
        wrapper.classList.remove('has-error');
      }
    });

    if (!valid) {
      window.MRG && window.MRG.toast({
        type: 'error',
        title: 'Lengkapi data terlebih dahulu',
        message: 'Beberapa field wajib pada General Information belum diisi.'
      });
      if (firstInvalid) firstInvalid.focus();
    }
    return valid;
  }

  function goTo(index) {
    if (index < 0 || index >= STEP_COUNT) return;
    if (index > current && !validateStep(current)) return;
    if (index > maxReached + 1) return; // don't allow skipping ahead beyond next unlocked step
    current = index;
    maxReached = Math.max(maxReached, current);
    renderRail();
    renderPanels();
  }

  function next() {
    if (current === STEP_COUNT - 1) {
      document.dispatchEvent(new CustomEvent('wizard:finish'));
      return;
    }
    if (!validateStep(current)) return;
    current += 1;
    maxReached = Math.max(maxReached, current);
    renderRail();
    renderPanels();
  }

  function back() {
    if (current === 0) return;
    current -= 1;
    renderRail();
    renderPanels();
  }

  function initNav() {
    const nextBtn = $('[data-wizard-next]');
    const backBtn = $('[data-wizard-back]');
    if (nextBtn) nextBtn.addEventListener('click', next);
    if (backBtn) backBtn.addEventListener('click', back);

    $all('.step-rail__node').forEach(function (node) {
      node.addEventListener('click', function () {
        goTo(Number(node.closest('.step-rail__item').dataset.stepIndex));
      });
    });
  }

  function initFilenameWatchers() {
    ['tagNumber', 'repairFinish', 'problemTitle', 'nama'].forEach(function (name) {
      const el = document.querySelector('[name="' + name + '"]');
      if (el) el.addEventListener('input', updateFilenamePreview);
    });
    document.addEventListener('select:change', updateFilenamePreview);
    document.addEventListener('generate-options:change', updateFilenamePreview);
  }

  function initGenerateAction() {
    document.addEventListener('wizard:finish', function () {
      const xlsxOn = $('[data-output-xlsx]') ? $('[data-output-xlsx]').classList.contains('is-checked') : true;
      const pdfOn = $('[data-output-pdf]') ? $('[data-output-pdf]').classList.contains('is-checked') : true;

      if (!xlsxOn && !pdfOn) {
        window.MRG && window.MRG.toast({ type: 'error', title: 'Pilih output', message: 'Pilih minimal satu format output (Excel atau PDF).' });
        return;
      }

      window.MRG && window.MRG.setLoading(true, 'Menyusun report…');
      window.setTimeout(function () {
        window.MRG && window.MRG.setLoading(false);
        window.MRG && window.MRG.toast({
          type: 'success',
          title: 'Report berhasil dibuat',
          message: 'Frontend prototype — backend generate akan disambungkan di tahap berikutnya.'
        });
      }, 1400);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!$('.step-rail')) return; // not on wizard page
    initNav();
    initFilenameWatchers();
    initGenerateAction();
    renderRail();
    renderPanels();
  });

  window.MRG = window.MRG || {};
  window.MRG.wizard = { goTo: goTo, next: next, back: back };
})();
