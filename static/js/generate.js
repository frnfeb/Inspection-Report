/**
 * Inspection Report by FRNFEB -- frontend/backend glue.
 *
 * This file supplies collectFormData() and initFormSubmit(), which the
 * rest of the frontend (report-form.js, upload.js, dropdown.js) did not
 * yet implement -- the submit button previously just showed a "coming
 * soon" toast. Nothing else in the existing frontend is modified.
 *
 * Backend contract:
 *   POST {API_BASE}/api/generate   body: JSON from collectFormData()
 *                                   -> { job_id, filename }
 *   GET  {API_BASE}/api/download/{job_id}/xlsx
 *   GET  {API_BASE}/api/download/{job_id}/pdf
 */
(function () {
  "use strict";

  // ============================================================
  // GANTI URL INI ke alamat backend kamu setelah deploy ke
  // Railway/Render (lihat DEPLOY.md). Contoh:
  // "https://nama-app-kamu.up.railway.app"
  // ============================================================
  var API_BASE = window.MRG_API_BASE || "https://ISI-URL-BACKEND-KAMU-DISINI";

  // Fields the frontend uses input[type=file] uploads for, keyed by the
  // data-upload-zone value; collected separately from FormData since file
  // zones store thumbnails as data-URLs on .upload-thumb elements, not as
  // real <input type=file> values (see upload.js).
  var PHOTO_ZONES = {
    before: "photoBefore",
    after: "photoAfter",
    additional: "photoAdditional",
  };

  function collectPhoto(zoneName) {
    var section = document.querySelector('[data-upload-zone="' + zoneName + '"]');
    if (!section) return null;
    var thumb = section.querySelector(".upload-thumb");
    return thumb ? thumb.dataset.src || null : null;
  }

  /**
   * Reads every named field in #reportForm into a plain JSON object
   * matching what the backend expects:
   *   - plain inputs/selects (including the custom-select hidden inputs
   *     from dropdown.js, which share the same `name`) -> scalar string
   *   - fields repeated with the SAME name (checkbox groups, and any
   *     name ending in "[]") -> array of strings, in DOM order
   *   - the 3 photo upload zones -> base64 data URLs (or null)
   */
  function collectFormData() {
    var form = document.getElementById("reportForm");
    var formData = new FormData(form);

    // names that appear more than once in the form must become arrays,
    // in the order they appear -- everything else stays scalar.
    var counts = {};
    for (var key of formData.keys()) {
      counts[key] = (counts[key] || 0) + 1;
    }

    var data = {};
    var seen = {};
    for (var pair of formData.entries()) {
      var name = pair[0];
      var value = pair[1];
      var isArrayField = counts[name] > 1 || name.endsWith("[]");
      var cleanName = name.endsWith("[]") ? name.slice(0, -2) : name;

      if (isArrayField) {
        if (!Array.isArray(data[cleanName])) data[cleanName] = [];
        data[cleanName].push(value);
      } else {
        data[cleanName] = value;
      }
    }

    for (var zone in PHOTO_ZONES) {
      data[PHOTO_ZONES[zone]] = collectPhoto(zone);
    }

    return data;
  }

  function updateFilenamePreview(data) {
    var chip = document.querySelector("[data-filename-chip]");
    if (!chip) return;
    var parts = [
      data.tagNo || "TagNo",
      (data.dateFinish || "").slice(0, 4) || "Tahun",
      (data.dateFinish || "").slice(5, 7) || "Bulan",
      (data.dateFinish || "").slice(8, 10) || "Tanggal",
      data.problemTitle || "ProblemTitle",
      data.nama || "Nama",
    ];
    chip.textContent = parts.join("_").replace(/\s+/g, "_");
  }

  function downloadFile(url, filename) {
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
  }

  async function handleSubmit(e) {
    e.preventDefault();
    var submitBtn = e.target.querySelector('button[type="submit"]');
    var originalLabel = submitBtn ? submitBtn.innerHTML : "";
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = "Membuat laporan...";
    }

    try {
      var data = collectFormData();
      updateFilenamePreview(data);

      var res = await fetch(API_BASE + "/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      if (!res.ok) {
        var errText = await res.text();
        throw new Error("Generate gagal (" + res.status + "): " + errText);
      }

      var result = await res.json();
      var jobId = result.job_id;
      var filename = result.filename || "Inspection_Report";

      downloadFile(API_BASE + "/api/download/" + jobId + "/xlsx", filename + ".xlsx");
      downloadFile(API_BASE + "/api/download/" + jobId + "/pdf", filename + ".pdf");

      if (window.MRG && window.MRG.toast) {
        window.MRG.toast({
          type: "success",
          title: "Berhasil",
          message: "Excel & PDF berhasil dibuat dan diunduh.",
        });
      }
    } catch (err) {
      console.error(err);
      if (window.MRG && window.MRG.toast) {
        window.MRG.toast({
          type: "error",
          title: "Gagal generate laporan",
          message: String(err.message || err),
        });
      } else {
        alert("Gagal generate laporan: " + (err.message || err));
      }
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalLabel;
      }
    }
  }

  function initFormSubmit() {
    var form = document.getElementById("reportForm");
    if (!form) return;
    form.addEventListener("submit", handleSubmit);
  }

  window.collectFormData = collectFormData;
  window.initFormSubmit = initFormSubmit;

  document.addEventListener("DOMContentLoaded", initFormSubmit);
})();
