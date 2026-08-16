# Arsitektur & Logika Sistem

Dokumen ini membedah rancangan *database* serta *business logic* mendasar yang diadopsi dalam proyek Absensi QR Code.

## 1. Struktur Database

Sistem memanfaatkan basis data relasional. Berikut adalah rancangan tabel utama:

### Tabel `siswa`
Menyimpan data master siswa.
- `id` (BIGINT, PK): Identifier unik (Auto Increment).
- `nis` (VARCHAR, UNIQUE): Nomor Induk Siswa.
- `nama` (VARCHAR): Nama Lengkap Siswa.
- `jurusan` (VARCHAR): Jurusan Siswa (Misal: RPL, TKJ).
- `kelas` (VARCHAR): Penanda spesifik kelas (Misal: X RPL 6).
- `kode_qr` (VARCHAR, UNIQUE): Kunci token QR yang direpresentasikan dalam format gambar QR (misal: `SISWA-XYZ123`).

### Tabel `absensi`
Merekam sejarah pemindaian kehadiran (scan).
- `id` (BIGINT, PK)
- `siswa_id` (BIGINT, FK ke `siswa(id)`)
- `nama`, `kelas`, `jurusan`: Denormalisasi data siswa pada saat absensi, mempermudah *query* laporan tanpa `JOIN` berat.
- `waktu` (VARCHAR): Jam kehadiran (`HH:MM`).
- `tanggal` (VARCHAR): Tanggal kehadiran (`YYYY-MM-DD`).
- `status` (VARCHAR): Status kehadiran (Hadir, Sakit, Izin, Alpha).
- **Constraint Unik**: Kombinasi `siswa_id` dan `tanggal` bersifat unik. Ini menjadi penjaga di level *database* agar **satu siswa hanya bisa terabsen satu kali per hari**.

## 2. Struktur Modul & Pola Desain (Application Factory)

Proyek ini telah direfaktor agar menggunakan *Application Factory* di Flask. Seluruh *logic* ditarik ke dalam folder `app/`:

```text
bulutangkistb26/
├── run.py                 # Titik masuk (entry point) aplikasi
├── app/
│   ├── __init__.py        # Berisi fungsi create_app()
│   ├── core/              # Konfigurasi, Koneksi DB, Utilities
│   ├── services/          # Logika Bisnis (Siswa, Absensi, Token)
│   ├── routes/            # Blueprint endpoints web
│   ├── static/            # File JS, CSS, Barcode
│   └── templates/         # Render HTML (Jinja2)
├── docs/                  # Dokumentasi Markdown
└── tests/                 # Kode Unit & Integration Test
```
**Mengapa Struktur Ini?**
- **Skalabilitas**: Jika sistem membesar (contohnya menambah modul Guru/Pegawai), *developer* cukup membuat berkas *service* dan *route* baru tanpa mengacaukan yang lain.
- **Isolasi Logika**: Fungsi koneksi (di `core/db.py`) terpisah murni dari aturan bisnis absen (di `services/absensi_service.py`).
- **Keamanan Variabel Lingkungan**: Rahasia aplikasi dimuat aman di modul terpusat (`config.py`).

## 3. Aturan "Khusus Hari Senin"

Sesuai permintaan proyek, absensi hanya diperbolehkan pada hari Senin.
- **Logika Layar Siswa**: Jika siswa login dan sistem mendeteksi hari ini *bukan* hari Senin, QR code tidak akan dirender. Akan muncul notifikasi informatif bahwa "Absensi Khusus Hari Senin".
- **Logika Scanner API**: Jika sebuah API scan dipanggil di luar hari Senin, servis akan merespons *error* (meskipun ini dapat ditimpa jika ada token Bypass, misal untuk hari Sabtu, yang dikelola di modul `token_service.py`).

## 4. Mekanisme Rekap & Performa

Modul `get_rekap_akumulasi_siswa` pada `absensi_service.py` melakukan perhitungan *real-time* dengan melakukan:
1. *Grouping* berdasarkan NIS/Nama Siswa.
2. Penjumlahan matriks status (Hadir, Izin, Sakit, Alpha).
3. Penjumlahan Total Pertemuan (khusus siswa tersebut).
Ini sangat efisien dan diexport seketika ke file `.xlsx` menggunakan `openpyxl`. Kinerja di TiDB Cloud dikompensasi menggunakan `pool_size=10` di SQLAlchemy untuk memastikan laporan dieksekusi dengan *overhead* minimum.
