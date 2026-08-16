# Panduan Setup Lokal

Panduan ini akan membantu Anda menjalankan proyek ini di mesin pengembangan lokal Anda.

## Prasyarat
- Python 3.10 atau versi lebih baru.
- Git.
- Koneksi internet (jika menggunakan TiDB Cloud).

## 1. Instalasi dan Persiapan Lingkungan

Buka terminal dan lakukan *clone* pada repositori ini jika belum:
```bash
git clone https://github.com/FARILtau72/bulutangkistb26.git
cd bulutangkistb26
```

Sebaiknya, buat *virtual environment* Python agar dependensi proyek ini terisolasi:
```bash
python -m venv venv

# Aktivasi di Windows:
venv\Scripts\activate

# Aktivasi di macOS/Linux:
source venv/bin/activate
```

Instal seluruh dependensi:
```bash
pip install -r requirements.txt
```

## 2. Konfigurasi Database (File `.env`)

Aplikasi ini menggunakan modul `python-dotenv` untuk memuat variabel lingkungan dari file `.env`.
Buat file bernama `.env` di *root directory* proyek, dan isi dengan kredensial TiDB Cloud Starter yang Anda miliki. 

Contoh isi `.env`:
```env
DB_PROVIDER=tidb
TIDB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=username.root
TIDB_PASSWORD=passwordAnda
TIDB_DATABASE=test
DB_AUTO_FALLBACK_SQLITE=0
```
*(Pastikan Anda merahasiakan kredensial ini dan tidak melakukan commit `.env` ke GitHub).*

## 3. Menjalankan Aplikasi

Setelah `.env` disiapkan, sistem akan otomatis membaca konfigurasi tersebut dan membangun skema *database* apabila tabel-tabel terkait belum ada (Siswa, Absensi, dll).

Untuk menjalankan server pengembangan:
```bash
python run.py
```

Aplikasi akan berjalan di `http://127.0.0.1:8080` (atau IP lokal Anda).
Anda dapat membuka *browser* dan mengakses antarmuka.

### Login Admin
Untuk mengakses panel administrasi, gunakan akun standar (periksa tabel kredensial atau logic di `auth_service.py` untuk detail *hardcoded* atau *database check* jika sudah diaktifkan). Secara default, pastikan membaca dokumentasi kode internal jika Anda baru pertama kali mengatur admin.

---
**Catatan Penting:** 
Skema TiDB memanfaatkan arsitektur `SQLAlchemy`. Proses *pooling* telah dioptimasi dengan `pool_recycle` sehingga koneksi tetap stabil meskipun ditinggal cukup lama tanpa aktivitas.
