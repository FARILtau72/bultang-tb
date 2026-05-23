# 📚 Dokumentasi Sistem Absensi QR Code SMK

## Daftar Isi

1. [Gambaran Umum](#gambaran-umum)
2. [Arsitektur Sistem](#arsitektur-sistem)
3. [Instalasi & Setup](#instalasi--setup)
4. [Konfigurasi](#konfigurasi)
5. [Sistem Autentikasi (RBAC)](#sistem-autentikasi-rbac)
6. [Fitur Token Senin](#fitur-token-senin)
7. [Alur Penggunaan](#alur-penggunaan)
8. [API Reference](#api-reference)
9. [Database Schema](#database-schema)
10. [Struktur File](#struktur-file)
11. [Troubleshooting](#troubleshooting)

---

## Gambaran Umum

Sistem Absensi QR Code SMK adalah platform absensi digital berbasis web yang menggunakan QR Code untuk mencatat kehadiran siswa. Sistem ini dibangun dengan **Flask** (Python) dan mendukung database **TiDB Cloud** maupun **SQLite** (fallback lokal).

### Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🔐 **Login RBAC** | Dua role: **Admin** dan **Siswa** dengan hak akses berbeda |
| 🎫 **Token Senin** | Admin generate token mingguan, siswa tukar token untuk QR |
| 📱 **QR Code Kondisional** | QR Code hanya muncul di hari Senin setelah tukar token |
| 📊 **Dashboard Admin** | Statistik kehadiran, grafik per jurusan, 10 absensi terakhir |
| 📋 **Kelola Absensi** | Admin bisa set status (Hadir/Sakit/Izin/Alpha) per siswa |
| 👨‍🎓 **CRUD Siswa** | Tambah, edit, hapus data siswa + generate QR otomatis |
| 📸 **Scan QR** | Admin scan QR Code siswa untuk mencatat kehadiran |
| 📁 **Rekap & Export** | Filter rekap absensi + export ke Excel |
| 🍪 **Persistent Login** | Remember me (30 hari) — login sekali, tetap tersimpan |

---

## Arsitektur Sistem

```
┌──────────────────────────────────────────────────────────┐
│                      BROWSER                             │
│  ┌─────────┐  ┌──────────────┐  ┌──────────────────┐    │
│  │  Login   │  │  Dashboard   │  │  Admin Absensi   │    │
│  │  Page    │  │  Siswa       │  │  (Status+Token)  │    │
│  └─────────┘  └──────────────┘  └──────────────────┘    │
└──────────────────────┬───────────────────────────────────┘
                       │ HTTP
┌──────────────────────┴───────────────────────────────────┐
│                    FLASK APP                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │  Routes   │  │ Services │  │  Auth    │               │
│  │  (7 BP)   │  │ (4 svc)  │  │ (RBAC)  │               │
│  └──────────┘  └──────────┘  └──────────┘               │
│  ┌──────────────────────────────────────┐               │
│  │          Flask-Login (Session)        │               │
│  └──────────────────────────────────────┘               │
└──────────────────────┬───────────────────────────────────┘
                       │ SQLAlchemy
┌──────────────────────┴───────────────────────────────────┐
│              DATABASE (TiDB / SQLite)                    │
│  ┌────────┐ ┌─────────┐ ┌────────────────┐ ┌──────────┐ │
│  │ siswa  │ │ absensi │ │ saturday_token │ │ token_   │ │
│  │        │ │         │ │                │ │ redemp.  │ │
│  └────────┘ └─────────┘ └────────────────┘ └──────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Timezone

Semua operasi tanggal dan waktu menggunakan **WIB (Asia/Jakarta, UTC+7)**.

| Fungsi | Lokasi | Output |
|--------|--------|--------|
| `get_now_wib()` | `utils.py` | `datetime` object dengan timezone WIB |
| `get_today_str()` | `utils.py` | `"2026-05-01"` (format YYYY-MM-DD) |
| `get_now_time_str()` | `utils.py` | `"20:30:45"` (format HH:MM:SS) |
| `weekday() == 0` | routes | Senin (Mon=0, Tue=1, ..., Sat=5, Sun=6) |

---

## Instalasi & Setup

### Prasyarat

- Python 3.11+
- pip

### Langkah Instalasi

```bash
# 1. Clone/download project
cd "ABSENSI QR CODE"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Konfigurasi .env (opsional — sudah ada default)
# Edit .env sesuai kebutuhan

# 4. Jalankan server
python app.py

# 5. Buka browser
# http://127.0.0.1:8080
```

### Dependencies

| Package | Versi | Fungsi |
|---------|-------|--------|
| Flask | ≥3.0.0 | Web framework |
| flask-login | ≥0.6.3 | Session & autentikasi |
| SQLAlchemy | ≥2.0.30 | ORM database |
| PyMySQL | ≥1.1.1 | Driver TiDB/MySQL |
| python-dotenv | ≥1.0.1 | Load .env file |
| qrcode | ≥7.4.2 | Generate QR Code |
| Pillow | ≥10.3.0 | Image processing |
| pandas | ≥2.2.2 | Data processing |
| openpyxl | ≥3.1.2 | Export Excel |

---

## Konfigurasi

### File `.env`

```env
# ═══════════════════════════════════════════
# DATABASE
# ═══════════════════════════════════════════
# Provider: "tidb" atau "sqlite"
DB_PROVIDER=tidb

# Fallback ke SQLite jika TiDB tidak tersedia
DB_AUTO_FALLBACK_SQLITE=1

# TiDB Cloud connection
TIDB_HOST=gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=your_user
TIDB_PASSWORD=your_password
TIDB_DATABASE=absensi_smk

# Optional: path ke CA cert
TIDB_SSL_CA=

# ═══════════════════════════════════════════
# AUTENTIKASI
# ═══════════════════════════════════════════
SECRET_KEY=smk-absensi-qrcode-secret

# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

# Berapa hari session "remember me" bertahan
REMEMBER_COOKIE_DAYS=30
```

### Password Hashing (Opsional)

Untuk keamanan lebih, gunakan hashed password di `.env`:

```bash
# Generate hash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('password_anda'))"

# Output contoh:
# scrypt:32768:8:1$abc123$def456...

# Paste ke .env:
ADMIN_PASSWORD=scrypt:32768:8:1$abc123$def456...
```

Sistem otomatis mendeteksi apakah `ADMIN_PASSWORD` berupa hash (dimulai `scrypt:` atau `pbkdf2:`) atau plaintext.

---

## Sistem Autentikasi (RBAC)

### Dua Role

| Role | Login Dengan | Hak Akses |
|------|-------------|-----------|
| **Admin** | Username + Password (dari `.env`) | Semua fitur |
| **Siswa** | Nama Lengkap + NIS | Dashboard sendiri + tukar token |

### Hak Akses Detail

| Halaman / Fitur | URL | Admin | Siswa | Anonim |
|-----------------|-----|:-----:|:-----:|:------:|
| Landing page | `/` | → Dashboard | → Dashboard Siswa | → Login |
| Login | `/login` | ✅ | ✅ | ✅ |
| Logout | `/logout` | ✅ | ✅ | — |
| Dashboard Admin | `/dashboard` | ✅ | ❌ | ❌ |
| Dashboard Siswa | `/siswa/dashboard` | ❌ | ✅ | ❌ |
| Daftar Siswa (CRUD) | `/siswa` | ✅ | ❌ | ❌ |
| Tambah Siswa | `/siswa/tambah` | ✅ | ❌ | ❌ |
| Edit Siswa | `/siswa/<id>/edit` | ✅ | ❌ | ❌ |
| Scan QR | `/scan` | ✅ | ❌ | ❌ |
| Rekap Absensi | `/rekap` | ✅ | ❌ | ❌ |
| Export Excel | `/rekap/export` | ✅ | ❌ | ❌ |
| Kelola Absensi | `/admin/absensi` | ✅ | ❌ | ❌ |
| Generate Token | `/api/admin/generate-token` | ✅ | ❌ | ❌ |
| Set Status | `/api/admin/set-status` | ✅ | ❌ | ❌ |
| Tukar Token | `/siswa/redeem-token` | ❌ | ✅ | ❌ |

### Persistent Login (Remember Me)

- Saat login, session disimpan selama **30 hari** (konfigurasi `REMEMBER_COOKIE_DAYS`)
- Siswa/admin cukup login **sekali** — tutup browser, buka lagi, tetap login
- Untuk logout manual: klik **Logout** di navbar

### Login Siswa

```
Input:  Nama Lengkap + NIS
Validasi: NIS exact match, Nama case-insensitive match
Contoh: Nama="Budi Santoso", NIS="12345"
```

> **Catatan**: Nama harus sesuai dengan yang terdaftar di database. Pencocokan bersifat case-insensitive (huruf besar/kecil tidak masalah).

### Login Admin

```
Input:  Username + Password
Default: admin / admin123
Sumber: File .env (ADMIN_USERNAME, ADMIN_PASSWORD)
```

---

## Fitur Token Senin

### Konsep

Setiap hari **Senin**, admin men-generate sebuah token unik (contoh: `SEN-A7X3`). Token ini diberikan kepada semua siswa. Siswa yang memasukkan token dengan benar di dashboard mereka akan mendapatkan QR Code untuk absensi hari itu.

### Alur Token

```
Admin                          Siswa
  │                              │
  ├── Generate Token ──────┐     │
  │   (SEN-XXXX)           │     │
  │                        │     │
  ├── Bagikan token ───────┼────►│
  │   (umumkan di kelas)   │     │
  │                        │     ├── Login (Nama + NIS)
  │                        │     │
  │                        │     ├── Masukkan token
  │                        │     │   (SEN-XXXX)
  │                        │     │
  │                        │     ├── Token valid?
  │                        │     │   ├── Ya → QR Code muncul
  │                        │     │   └── Tidak → Error
  │                        │     │
  │                        │     ├── Tunjukkan QR ke scanner
  │                        │     │
  ├── Scan QR siswa ◄──────┼─────┤
  │                        │     │
  ├── Absensi tercatat ────┘     │
  │                              │
```

### Aturan Token

| Aturan | Detail |
|--------|--------|
| **Siapa yang generate?** | Admin, melalui halaman `/admin/absensi` |
| **Kapan bisa generate?** | Kapan saja (admin bisa persiapan sebelum Senin) |
| **Format token** | `SEN-XXXX` (4 karakter acak alfanumerik) |
| **Berlaku berapa lama?** | Hanya untuk tanggal saat di-generate |
| **Bisa regenerate?** | Ya — token lama diganti token baru |
| **1 token untuk?** | Semua siswa (token sama untuk semua) |
| **Kapan siswa bisa tukar?** | Hanya di hari **Senin** |
| **Siswa tukar berapa kali?** | 1x per hari (tercatat di `token_redemption`) |

### Dashboard Siswa — 4 Kondisi

| Kondisi | Tampilan |
|---------|----------|
| Bukan hari Senin | 📅 "QR Code Belum Tersedia — kembali hari Senin" |
| Senin, admin belum generate token | ⏳ "Menunggu Token dari Admin" |
| Senin, token sudah ada, siswa belum tukar | 🎫 Form input token |
| Senin, siswa sudah tukar token | ✅ QR Code besar + info absensi |

---

## Alur Penggunaan

### Alur Harian (Hari Senin)

```
┌─────────────────────────────────────────┐
│          PERSIAPAN (Admin)              │
│                                         │
│  1. Login sebagai admin                 │
│  2. Buka /admin/absensi                 │
│  3. Klik "Generate Token"               │
│  4. Catat/copy token (SEN-XXXX)         │
│  5. Umumkan token ke siswa              │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          ABSENSI SISWA (Siswa)          │
│                                         │
│  1. Buka app / login (Nama + NIS)       │
│  2. Masukkan token dari admin           │
│  3. QR Code muncul                      │
│  4. Tunjukkan QR ke scanner admin       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          SCANNING (Admin)               │
│                                         │
│  1. Buka /scan                          │
│  2. Arahkan kamera ke QR siswa          │
│  3. Sistem otomatis catat kehadiran     │
│  4. Status: HADIR                       │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│          MANUAL STATUS (Admin)          │
│                                         │
│  Untuk siswa yang tidak scan:           │
│  1. Buka /admin/absensi                 │
│  2. Pilih status dari dropdown          │
│     (Sakit / Izin / Alpha)              │
│  3. Status otomatis tersimpan (AJAX)    │
└─────────────────────────────────────────┘
```

### Alur Non-Senin

- **Siswa**: Login → melihat pesan "QR belum tersedia" → tidak bisa tukar token
- **Admin**: Login → bisa akses semua fitur kecuali scan QR siswa (tidak ada QR)
- **Admin**: Bisa persiapkan token untuk Senin mendatang

---

## API Reference

### Autentikasi

| Method | URL | Body | Response | Auth |
|--------|-----|------|----------|------|
| `GET` | `/login` | — | Halaman login | Public |
| `POST` | `/login` | `login_type`, `nama`/`nis` atau `username`/`password` | Redirect | Public |
| `GET` | `/logout` | — | Redirect ke `/login` | Login |

### Token API (Admin Only)

| Method | URL | Body | Response |
|--------|-----|------|----------|
| `POST` | `/api/admin/generate-token` | — | `{"status":"success","token":"SEN-XXXX","tanggal":"2026-05-01"}` |
| `GET` | `/api/admin/today-token` | — | `{"status":"success","token":{...}}` |

### Absensi API (Admin Only)

| Method | URL | Body | Response |
|--------|-----|------|----------|
| `POST` | `/api/admin/set-status` | `{"siswa_id":1,"status":"HADIR"}` | `{"status":"success","message":"..."}` |

**Status yang valid**: `HADIR`, `SAKIT`, `IZIN`, `ALPHA`

### Token Redemption (Siswa Only)

| Method | URL | Body | Response |
|--------|-----|------|----------|
| `POST` | `/siswa/redeem-token` | `{"token":"SEN-XXXX"}` | `{"status":"success"}` atau `{"status":"error"}` |

### Scan API (Admin Only)

| Method | URL | Body | Response |
|--------|-----|------|----------|
| `POST` | `/api/process_scan` | `{"code":"SISWA-12345-ABCD","status":"HADIR"}` | `{"status":"success","nama":"..."}` |

### Siswa API (Admin Only)

| Method | URL | Body | Response |
|--------|-----|------|----------|
| `GET` | `/api/kelas?jurusan=RPL` | — | `{"jurusan":"RPL","kelas":[...]}` |
| `POST` | `/siswa/<id>/regenerate_qr` | — | `{"status":"success","siswa":{...}}` |
| `POST` | `/siswa/<id>/delete` | — | `{"status":"success","redirect":"..."}` |

---

## Database Schema

### Tabel `siswa`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INTEGER/BIGINT PK | Auto increment |
| `nis` | TEXT/VARCHAR(64) | Nomor Induk Siswa (UNIQUE) |
| `nama` | TEXT/VARCHAR(255) | Nama lengkap |
| `jurusan` | TEXT/VARCHAR(20) | RPL / TAV / TKR / TITL |
| `kelas` | TEXT/VARCHAR(50) | Contoh: "X RPL 1" |
| `kode_qr` | TEXT/VARCHAR(255) | Kode QR unik (UNIQUE) |

### Tabel `absensi`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INTEGER/BIGINT PK | Auto increment |
| `siswa_id` | INTEGER/BIGINT FK | → siswa.id |
| `nama` | TEXT/VARCHAR(255) | Nama siswa (denormalisasi) |
| `kelas` | TEXT/VARCHAR(50) | Kelas siswa |
| `jurusan` | TEXT/VARCHAR(20) | Jurusan siswa |
| `waktu` | TEXT/VARCHAR(16) | Jam absensi (HH:MM:SS) |
| `tanggal` | TEXT/VARCHAR(16) | Tanggal (YYYY-MM-DD) |
| `status` | TEXT/VARCHAR(10) | HADIR / SAKIT / IZIN / ALPHA |

**Constraint**: UNIQUE(siswa_id, tanggal) — 1 siswa hanya bisa 1 absensi per hari.

### Tabel `saturday_token`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INTEGER/BIGINT PK | Auto increment |
| `token` | TEXT/VARCHAR(20) | Kode token (SEN-XXXX) |
| `tanggal` | TEXT/VARCHAR(16) | Tanggal Senin (UNIQUE) |
| `created_at` | TEXT/VARCHAR(30) | Waktu pembuatan |

### Tabel `token_redemption`

| Kolom | Tipe | Keterangan |
|-------|------|------------|
| `id` | INTEGER/BIGINT PK | Auto increment |
| `siswa_id` | INTEGER/BIGINT FK | → siswa.id |
| `tanggal` | TEXT/VARCHAR(16) | Tanggal penukaran |
| `redeemed_at` | TEXT/VARCHAR(30) | Waktu penukaran |

**Constraint**: UNIQUE(siswa_id, tanggal) — 1 siswa hanya bisa tukar 1x per hari.

### Relasi

```
siswa (1) ──── (N) absensi
siswa (1) ──── (N) token_redemption
saturday_token: standalone (1 token per tanggal)
```

---

## Struktur File

```
ABSENSI QR CODE/
├── .env                        # Konfigurasi environment
├── app.py                      # Flask app factory + Flask-Login init
├── config.py                   # Konfigurasi global (DB, auth, kelas)
├── db.py                       # Database engine + schema creation
├── models.py                   # Re-export module (backward compat)
├── requirements.txt            # Dependencies
│
├── auth_service.py             # [NEW] User model, login, RBAC decorators
├── token_service.py            # [NEW] Token generate/validate/redeem
├── siswa_service.py            # CRUD siswa + QR generation
├── absensi_service.py          # Absensi logic + manual status
├── utils.py                    # Datetime helpers (WIB timezone)
│
├── routes/
│   ├── __init__.py             # Blueprint registration
│   ├── auth.py                 # [NEW] Login/logout routes
│   ├── admin.py                # [NEW] Admin absensi + token API
│   ├── siswa_dashboard.py      # [NEW] Dashboard siswa + token redeem
│   ├── dashboard.py            # Dashboard admin (stats + grafik)
│   ├── siswa.py                # CRUD siswa (admin-only)
│   ├── scan.py                 # QR scanner (admin-only)
│   └── rekap.py                # Rekap + export (admin-only)
│
├── templates/
│   ├── layout.html             # Base template + dynamic navbar
│   ├── login.html              # [NEW] Halaman login (2 tab)
│   ├── siswa_dashboard.html    # [NEW] Dashboard siswa (QR kondisional)
│   ├── admin_absensi.html      # [NEW] Kelola absensi + token
│   ├── dashboard.html          # Dashboard admin
│   ├── siswa_list.html         # Daftar siswa
│   ├── siswa_add.html          # Form tambah siswa
│   ├── siswa_edit.html         # Form edit siswa
│   ├── scan.html               # Scanner QR
│   └── rekap.html              # Tabel rekap
│
├── static/
│   ├── css/style.css           # Stylesheet utama
│   ├── js/app.js               # JavaScript utama
│   └── barcodes/               # Generated QR images
│
└── absensi.db                  # SQLite database (lokal)
```

---

## Troubleshooting

### Login gagal (siswa)

| Masalah | Solusi |
|---------|--------|
| "Nama atau NIS salah" | Pastikan nama **persis** seperti di database (spasi, ejaan). NIS harus exact match. |
| Nama benar tapi tetap gagal | Coba dengan huruf kecil semua — sistem case-insensitive |
| NIS tidak ditemukan | Pastikan siswa sudah ditambahkan oleh admin di `/siswa/tambah` |

### Login gagal (admin)

| Masalah | Solusi |
|---------|--------|
| "Username atau password salah" | Default: `admin` / `admin123`. Cek `.env` |
| Setelah ganti password hash | Pastikan format hash dimulai `scrypt:` atau `pbkdf2:` |

### QR Code tidak muncul

| Masalah | Solusi |
|---------|--------|
| "QR Code Belum Tersedia" | Normal jika bukan hari Senin |
| "Menunggu Token dari Admin" | Admin belum generate token — hubungi admin |
| Token salah | Periksa kembali token (huruf besar, angka). Format: `SEN-XXXX` |

### Token tidak bisa di-generate

| Masalah | Solusi |
|---------|--------|
| Tombol tidak ada | Cek apakah login sebagai admin (bukan siswa) |
| Error saat generate | Periksa koneksi database |

### Database

| Masalah | Solusi |
|---------|--------|
| TiDB connection failed | Cek `.env` credentials. Sistem auto-fallback ke SQLite |
| Schema error | Hapus `absensi.db`, restart app — schema otomatis dibuat ulang |
| Data hilang setelah deploy | Jika pakai Vercel, data SQLite hilang (ephemeral). Gunakan TiDB |

---

## Catatan Teknis

### Keamanan

- **Password admin**: Mendukung hashing dengan `werkzeug.security` (scrypt/pbkdf2)
- **Session**: Menggunakan Flask-Login dengan signed cookies
- **RBAC**: Semua route dilindungi decorator `@admin_required` atau `@siswa_required`
- **CSRF**: Form menggunakan POST method
- **SQL Injection**: Dicegah dengan parameterized queries (SQLAlchemy `text()` + bind params)

### Performa

- **Database**: Connection pooling via SQLAlchemy engine
- **Auto-fallback**: TiDB → SQLite otomatis jika TiDB tidak tersedia
- **QR Generation**: File PNG disimpan di disk, served via static route

### Kompatibilitas Browser

- Chrome, Firefox, Safari, Edge (modern)
- Responsive design (Bootstrap 5.3)
- Mobile-friendly (QR scanner, dashboard)
