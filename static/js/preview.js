/* ==========================================================================
   preview.js — right-hand PDF preview panel
   Tabs: inspection | cplpump | photo — reflects live form data where possible,
   falls back to dummy data so the preview never looks empty.
   ========================================================================== */

(function () {
  'use strict';

  const TABS = ['inspection', 'cplpump', 'photo'];
  const TAB_LABELS = { inspection: 'Inspection Report', cplpump: 'CPL Pump', photo: 'Bukti Foto' };
  let activeTab = 'inspection';

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $all(sel, ctx) { return Array.from((ctx || document).querySelectorAll(sel)); }

  function fieldVal(name, fallback) {
    const el = document.querySelector('[name="' + name + '"]');
    const v = el ? (el.value || '').trim() : '';
    return v || fallback;
  }

  function enabledSheets() {
    return {
      inspection: $('[data-sheet-inspection]') ? $('[data-sheet-inspection]').classList.contains('is-checked') : true,
      cplpump: $('[data-sheet-cplpump]') ? $('[data-sheet-cplpump]').classList.contains('is-checked') : true,
      photo: $('[data-sheet-photo]') ? $('[data-sheet-photo]').classList.contains('is-checked') : true
    };
  }

  /* ---------------- Cover info block (shared across tabs) ---------------- */
  function coverGridHtml() {
    const rows = [
      ['Nama', fieldVal('nama', 'Farhan')],
      ['Plant', fieldVal('plant', 'CA-1')],
      ['Tag Number', fieldVal('tagNumber', 'KB-101')],
      ['Equipment', fieldVal('equipment', 'Centrifugal Pump')],
      ['Activity', fieldVal('activity', 'Overhaul')],
      ['PIC', fieldVal('pic', 'Farhan')],
      ['Repair Start', fieldVal('repairStart', '28 Jul 2026')],
      ['Repair Finish', fieldVal('repairFinish', '29 Jul 2026')]
    ];
    return rows.map(function (r) {
      return '<div class="pdf-cell"><label>' + r[0] + '</label><span>' + r[1] + '</span></div>';
    }).join('') +
      '<div class="pdf-cell full"><label>Problem Title at Request Slip</label><span>' + fieldVal('problemTitle', 'Bearing Failure') + '</span></div>';
  }

  /* ---------------- Inspection tab ---------------- */
  function selectedCards(groupSelector) {
    return $all(groupSelector + ' .card-check.is-selected').map(function (c) {
      return c.querySelector('.card-check__text').textContent.trim();
    });
  }

  function causeListHtml(title, items, dummyItems) {
    const list = items.length ? items : dummyItems;
    const isDummy = items.length === 0;
    return '<div class="pdf-cell full">' +
      '<label>' + title + (isDummy ? ' (contoh)' : '') + '</label>' +
      '<span>' + (list.length ? list.join(', ') : 'Belum ada yang dipilih') + '</span>' +
      '</div>';
  }

  function renderInspectionTab() {
    const direct = selectedCards('[data-cause-group="direct"]');
    const root = selectedCards('[data-cause-group="root"]');

    return (
      '<div class="pdf-sheet">' +
      pdfBrandHtml('Summary of Inspection Sheet') +
      '<div class="pdf-grid">' + coverGridHtml() + '</div>' +
      '<div class="pdf-section-title">Direct &amp; Root Cause</div>' +
      '<div class="pdf-grid">' +
      causeListHtml('Direct Cause', direct, ['Machine (ME)']) +
      causeListHtml('Root Cause', root, ['Bad Scheduling (BS)']) +
      '</div>' +
      '<div class="pdf-section-title">Description &amp; Recommendation</div>' +
      '<div class="pdf-grid">' +
      '<div class="pdf-cell full"><label>Description</label><span>' + fieldVal('description', 'Ditemukan getaran tinggi pada bearing DE saat patrol rutin.') + '</span></div>' +
      '<div class="pdf-cell full"><label>Recommendation</label><span>' + fieldVal('recommendation', 'Pasang sensor vibrasi online untuk monitoring berkelanjutan.') + '</span></div>' +
      '</div>' +
      '</div>'
    );
  }

  /* ---------------- CPL Pump tab ---------------- */
  function renderCplPumpTab() {
    const items = $all('.accordion-item');
    let rows = '';

    if (items.length === 0) {
      rows = '<tr><td colspan="2">Belum ada komponen</td></tr>';
    } else {
      rows = items.map(function (item) {
        const name = $('.accordion-item__title strong', item).textContent.trim();
        const checked = $all('.card-check.is-selected', item).map(function (c) {
          return c.querySelector('.card-check__text').textContent.trim();
        });
        return '<tr><td style="width:34%"><strong>' + name + '</strong></td><td>' +
          (checked.length ? checked.join(', ') : '<span style="color:#aaa">Tidak ada item dicentang</span>') +
          '</td></tr>';
      }).join('');
    }

    return (
      '<div class="pdf-sheet">' +
      pdfBrandHtml('CPL Pump Checklist') +
      '<div class="pdf-section-title">Component Checklist</div>' +
      '<table class="pdf-table"><thead><tr><th>Component</th><th>Checked items</th></tr></thead><tbody>' + rows + '</tbody></table>' +
      '</div>'
    );
  }

  /* ---------------- Photo tab ---------------- */
  const cameraIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>';

  function photoSlotsHtml(zoneName) {
    const section = document.querySelector('[data-upload-zone="' + zoneName + '"]');
    const thumbs = section ? $all('.upload-thumb', section) : [];
    let html = '';
    const count = Math.max(thumbs.length, 3);
    for (let i = 0; i < Math.min(count, 6); i++) {
      const thumb = thumbs[i];
      if (thumb) {
        html += '<div class="pdf-photo-slot has-img"><img src="' + thumb.dataset.src + '" alt=""></div>';
      } else {
        html += '<div class="pdf-photo-slot">' + cameraIcon + '</div>';
      }
    }
    return html;
  }

  function renderPhotoTab() {
    return (
      '<div class="pdf-sheet">' +
      pdfBrandHtml('Bukti Foto') +
      '<div class="pdf-section-title">Before Repair</div>' +
      '<div class="pdf-photo-grid">' + photoSlotsHtml('before') + '</div>' +
      '<div class="pdf-section-title">After Repair</div>' +
      '<div class="pdf-photo-grid">' + photoSlotsHtml('after') + '</div>' +
      '<div class="pdf-section-title">Additional</div>' +
      '<div class="pdf-photo-grid">' + photoSlotsHtml('additional') + '</div>' +
      '</div>'
    );
  }

  function pdfBrandHtml(subtitle) {
    return (
      '<div class="pdf-sheet__brand">' +
      '<div class="mark"></div>' +
      '<div><strong>Maintenance Report Generator</strong><span>' + subtitle + '</span></div>' +
      '<div class="pdf-doc-no">No: FRM-MRT-XXXX<br>Rev: 0</div>' +
      '</div>' +
      '<div class="pdf-sheet__title">' + fieldVal('tagNumber', 'KB-101') + ' — ' + fieldVal('problemTitle', 'Bearing Failure') + '</div>'
    );
  }

  const RENDERERS = { inspection: renderInspectionTab, cplpump: renderCplPumpTab, photo: renderPhotoTab };

  function renderEmptyState(tab) {
    return '<div class="pdf-empty">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/></svg>' +
      '<strong>' + TAB_LABELS[tab] + ' tidak disertakan</strong>' +
      '<span>Centang sheet ini di Step 5 — Generate untuk menampilkannya di PDF.</span>' +
      '</div>';
  }

  function renderActiveTab() {
    const body = $('[data-preview-body]');
    if (!body) return;
    const sheets = enabledSheets();

    body.innerHTML = sheets[activeTab] ? RENDERERS[activeTab]() : renderEmptyState(activeTab);

    $all('.preview-tab').forEach(function (tab) {
      tab.classList.toggle('is-active', tab.dataset.previewTab === activeTab);
      tab.classList.toggle('is-disabled', !sheets[tab.dataset.previewTab]);
    });

    const idx = TABS.indexOf(activeTab);
    const pageLabel = $('[data-preview-page-label]');
    if (pageLabel) pageLabel.textContent = 'Halaman ' + (idx + 1) + ' dari ' + TABS.length;

    const prevBtn = $('[data-preview-prev]');
    const nextBtn = $('[data-preview-next]');
    if (prevBtn) prevBtn.disabled = idx === 0;
    if (nextBtn) nextBtn.disabled = idx === TABS.length - 1;
  }

  function setTab(tab) {
    activeTab = tab;
    renderActiveTab();
  }

  function initTabs() {
    $all('.preview-tab').forEach(function (tabBtn) {
      tabBtn.addEventListener('click', function () { setTab(tabBtn.dataset.previewTab); });
    });

    const prevBtn = $('[data-preview-prev]');
    const nextBtn = $('[data-preview-next]');
    if (prevBtn) prevBtn.addEventListener('click', function () {
      const idx = TABS.indexOf(activeTab);
      if (idx > 0) setTab(TABS[idx - 1]);
    });
    if (nextBtn) nextBtn.addEventListener('click', function () {
      const idx = TABS.indexOf(activeTab);
      if (idx < TABS.length - 1) setTab(TABS[idx + 1]);
    });
  }

  function initMobileToggle() {
    const toggleBtn = $('[data-preview-toggle]');
    const panel = $('.preview-panel');
    if (!toggleBtn || !panel) return;
    toggleBtn.addEventListener('click', function () {
      panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  function initLiveUpdates() {
    document.body.addEventListener('input', function (e) {
      if (e.target.closest('.form-panel')) renderActiveTab();
    });
    document.addEventListener('select:change', renderActiveTab);
    document.addEventListener('inspection:change', renderActiveTab);
    document.addEventListener('cplpump:change', renderActiveTab);
    document.addEventListener('upload:change', renderActiveTab);
    document.addEventListener('generate-options:change', renderActiveTab);
  }

  document.addEventListener('DOMContentLoaded', function () {
    if (!$('[data-preview-body]')) return;
    initTabs();
    initMobileToggle();
    initLiveUpdates();
    renderActiveTab();
  });
})();
