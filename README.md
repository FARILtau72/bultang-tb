# Sistem Absensi QR Code (Senin Saja)

Aplikasi web berbasis Flask untuk mengelola absensi siswa sekolah menggunakan teknologi QR Code. Aplikasi ini didesain khusus dengan aturan bahwa *scan absensi dan akses barcode siswa hanya terbuka pada hari Senin*.

## Fitur Utama

1. **Dashboard Siswa (Tanpa PIN)**
   - Siswa cukup mengakses halaman web untuk melihat QR Code mereka.
   - QR Code hanya muncul pada hari Senin (WIB). Di hari lain, akses QR ditutup dengan pesan informatif.

2. **Scanner Absensi (Admin)**
   - Mendukung scanning via kamera *smartphone* atau *webcam* menggunakan pustaka `html5-qrcode`.
   - Proses scan super cepat, tervalidasi langsung terhadap *database* siswa.
   - Deteksi *duplicate scan* per hari, sehingga satu siswa hanya bisa terabsen sekali di hari tersebut.

3. **Dashboard Admin & Rekapitulasi**
   - Manajemen Data Siswa (Tambah, Edit, Hapus, Generate QR Code batch).
   - Live view hasil scan absensi hari ini.
   - **Rekap Akumulasi:** Generate laporan rekapitulasi kehadiran per kelas atau keseluruhan.
   - **Export Excel:** Laporan yang dapat diunduh dalam format `.xlsx` dengan format rapi dan siap cetak.

4. **Database Fleksibel & Scalable**
   - Mendukung **TiDB Cloud (MySQL)** untuk *production* yang ringan dan cepat berkat implementasi koneksi yang dipool (SQLAlchemy).
   - Memiliki *auto-fallback* ke SQLite jika konfigurasi TiDB belum diatur (sangat berguna untuk *development* awal).

## Struktur Proyek

Aplikasi ini menggunakan pola **Application Factory** standar Flask untuk menjaga agar kode terstruktur, mudah dites, dan *scalable*.

- `app/core/`: Berisi logika mendasar aplikasi seperti koneksi DB, konfigurasi, model data, dan utilitas.
- `app/services/`: Mengandung *business logic* (layanan absensi, siswa, autentikasi).
- `app/routes/`: Definisi semua *endpoint* HTTP (Blueprints).
- `docs/`: Dokumentasi detail pengembangan.
- `tests/`: Skrip *automated testing*.

## Mulai Menggunakan

Untuk instruksi instalasi, *setup database*, dan cara menjalankan proyek di komputer lokal, silakan merujuk ke dokumentasi berikut:

- [Panduan Setup Lokal (setup.md)](docs/setup.md)
- [Arsitektur & Konsep (architecture.md)](docs/architecture.md)

---
*Dibuat untuk memudahkan operasional presensi sekolah modern secara instan dan paperless.*
