# Cara Deploy — Frontend + Backend Jadi Satu, ke Railway

Frontend & backend sekarang digabung jadi satu aplikasi (frontend
ditaruh di folder `static/`, di-serve langsung sama backend Python-nya).
Jadi cukup **1x deploy** ke Railway, gak perlu Netlify sama sekali,
gak perlu urus CORS atau tempel-tempel URL manual.

## Langkah-langkah

1. Buka [github.com](https://github.com), daftar/login kalau belum
   punya akun.
2. Klik **+** di kanan atas → **New repository** → kasih nama (misal
   `inspection-report-app`) → **Create repository**.
3. Di halaman repo yang baru, klik link **uploading an existing file**.
4. Drag & drop **semua isi folder `backend/`** ke situ — `Dockerfile`,
   folder `app/`, folder `static/` (ini frontend-nya), folder
   `template/`, `requirements.txt`. Persis kayak drag-drop ke Netlify,
   gak perlu command line.
   - Folder `jobs/` gak usah diupload, itu cuma sampah sementara.
5. Scroll bawah, klik **Commit changes**.
6. Buka [railway.app](https://railway.app), login (bisa pakai akun
   GitHub) → **New Project** → **Deploy from GitHub repo** → pilih repo
   yang tadi.
7. Railway otomatis detect `Dockerfile` dan build sendiri (install
   Python + LibreOffice). Tunggu ~3-8 menit sampai status jadi
   "Deployed".
8. Klik project-nya → tab **Settings** → **Networking** → klik
   **Generate Domain**. Muncul URL kayak:
   ```
   https://inspection-report-app-production.up.railway.app
   ```
9. **Buka URL itu langsung di browser** — harusnya langsung muncul
   dashboard form-nya (bukan halaman API doang). Coba isi form, klik
   **Generate Excel & PDF**, harusnya langsung download 2 file.

Selesai. Satu URL itu aja yang dipakai/dibagiin ke tim kamu.

## Kalau nanti mau pisah lagi (opsional)

Kalau suatu saat mau frontend-nya tetap di Netlify (misal biar domain
custom-nya gampang), tinggal:
1. Upload folder `static/` isinya ke Netlify seperti biasa.
2. Buka `static/js/generate.js`, isi baris `API_BASE` dengan URL
   Railway kamu (bukan string kosong lagi).

Tapi kalau gak ada kebutuhan khusus, cara "jadi satu" di atas lebih
simpel — gak perlu dua tempat.

## Kalau ada error

- **Build gagal di Railway** → tab **Deployments** → **View Logs**,
  biasanya kelihatan errornya di situ.
- **Buka URL malah error/blank** → cek lagi apakah folder `static/`
  keupload dengan benar (harus ada `static/index.html`).
- **Generate gagal (klik tombol, muncul error)** → klik kanan browser →
  **Inspect** → tab **Console**/**Network**, lihat pesan errornya.
- **Lama banget pas generate** → normal, proses LibreOffice-nya makan
  waktu ~10-20 detik. Kalau baru pertama kali buka setelah lama
  nganggur (di paket gratis), bisa lebih lama lagi karena server lagi
  "dibangunkan".

## Catatan biaya

Railway kasih free trial credit ($5), abis itu bayar sesuai pemakaian —
untuk backend kecil yang jarang dipakai biasanya $1-5/bulan. Cukup buat
pemakaian internal kantor yang gak generate ratusan laporan sekaligus.
