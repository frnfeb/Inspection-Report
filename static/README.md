# Maintenance Report Generator — Frontend (Tahap 1)

Prototype UI murni frontend (HTML5 + CSS3 + Vanilla JS, tanpa framework/build
tool) untuk menggantikan pengisian report Excel secara manual. Tahap ini
**belum** tersambung ke backend — semua data hanya hidup di browser selama
sesi berlangsung, dan tombol Generate di step terakhir hanya mensimulasikan
proses (toast "berhasil") tanpa benar-benar membuat file.

## Cara menjalankan

Karena beberapa fitur (fetch font, module path) butuh HTTP, jangan buka
`index.html` langsung lewat `file://`. Jalankan static server sederhana dari
folder `frontend/`:

```bash
cd frontend
python3 -m http.server 8080
# atau: npx serve .
```

Lalu buka `http://localhost:8080`.

## Struktur folder

```
frontend/
├── index.html              Dashboard
├── pages/
│   ├── report-form.html  Wizard 5 step + preview PDF (halaman utama)
│   ├── inspection-report.html   Daftar report (dummy)
│   └── tutorial.html       Panduan pemakaian
├── css/
│   ├── style.css           Design tokens, reset, sidebar, topbar, tombol, toast
│   ├── wizard.css          Step rail, progress bar, layout wizard
│   ├── form.css            Input, dropdown searchable, card-checkbox, accordion, upload, generate
│   └── responsive.css      Breakpoint tablet (≤1180px) & mobile (≤760px)
├── js/
│   ├── app.js               Sidebar collapse/drawer, ripple, toast, loading overlay
│   ├── wizard.js            Navigasi step, progress rail, validasi, preview nama file
│   ├── preview.js           Panel preview PDF (tab + live data + dummy fallback)
│   ├── upload.js             Drag-drop upload, thumbnail, hapus foto
│   ├── dropdown.js           Searchable select + opsi "Custom"
│   └── checkbox.js           Card-checkbox, accordion, toggle/radio (Generate step)
└── assets/
    ├── logo/logo-mark.svg
    ├── icons/               (icon pakai Lucide via CDN — lihat README di dalam folder ini)
    └── images/
```

## Yang sudah berfungsi (klik-coba langsung)

- **Sidebar**: collapse (desktop), drawer (mobile), state tersimpan di localStorage.
- **Wizard**: Next/Back, step rail bisa diklik untuk step yang sudah dilewati,
  progress bar & rail bergerak, validasi field wajib di General Information.
- **Dropdown searchable**: ketik untuk filter, plus opsi "Custom…" yang
  memunculkan textbox bebas (Plant, Activity, PIC).
- **Card-checkbox**: Direct Cause / Root Cause, klik kartu untuk pilih,
  ada search, counter otomatis update.
- **Accordion CPL Pump**: 5 komponen (Bearing DE/NDE, Mechanical Seal,
  Impeller, Shaft), tiap komponen checklist sendiri, progress badge, search.
- **Upload foto**: drag & drop atau klik, 3 zona (Before/After/Additional),
  preview thumbnail, hapus foto, validasi tipe & ukuran file (maks 10MB).
- **Generate step**: toggle sheet (Inspection/CPL Pump/Bukti Foto), pilihan
  paper size (Letter/A4), toggle output (Excel/PDF), **preview nama file
  otomatis** mengikuti format `TagNo_Tahun_Bulan_Tanggal_ProblemTitle_Nama`
  dari data yang sudah diisi.
- **Preview PDF (panel kanan)**: 3 tab (Inspection/CPL Pump/Bukti Foto),
  data diambil langsung dari form yang sedang diisi (live), jatuh ke dummy
  data kalau field masih kosong. Kalau sebuah sheet di-uncheck di step
  Generate, tab-nya otomatis menampilkan status "tidak disertakan" —
  mensimulasikan efeknya ke PDF asli.
- **Responsive**: sudah diuji di lebar 1440px (desktop), tablet, dan 375px
  (mobile) — sidebar jadi drawer, layout wizard jadi satu kolom, preview
  bisa dipanggil lewat tombol mengambang di kanan bawah.
- **UX**: loading overlay, ripple di semua `.btn`, toast notification,
  animasi transisi antar step & saat panel dropdown/accordion terbuka.

## Yang sengaja belum dibuat (nunggu arahan tahap berikutnya)

- Tidak ada backend/API — tombol "Selesai" di step Generate hanya
  menampilkan toast simulasi.
- Data tidak persisten lintas reload (belum ada localStorage untuk isi form,
  hanya untuk preferensi sidebar).
- Autentikasi/login belum ada.

## Catatan implementasi

- Font **Inter** & icon **Lucide** dimuat dari CDN (Google Fonts, unpkg) —
  butuh koneksi internet saat membuka halaman.
- Semua komponen dibangun manual (bukan library UI) sesuai permintaan
  "Vanilla JavaScript tanpa React".
- Konvensi state: setiap komponen interaktif membaca/menulis lewat atribut
  `data-*` dan CustomEvent (`select:change`, `inspection:change`,
  `cplpump:change`, `upload:change`, `generate-options:change`,
  `wizard:stepchange`) — jadi gampang disambungkan ke logic backend nanti
  tanpa bongkar ulang markup.
