import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from app.core.models import add_siswa, list_siswa, set_manual_status, get_rekap_akumulasi_siswa, export_rekap_excel

students_data = [
    {"nis": "25210385", "nama": "FARIL PUTRA PRATAMA", "jurusan": "RPL", "kelas": "X RPL 6"},
    {"nis": "25210386", "nama": "Arga Kurniawan", "jurusan": "RPL", "kelas": "X RPL 6"},
    {"nis": "25210387", "nama": "Adam Prasetyo", "jurusan": "RPL", "kelas": "X RPL 4"},
    {"nis": "25210388", "nama": "Ahmad Aqil Nurhadi", "jurusan": "RPL", "kelas": "X RPL 6"},
    {"nis": "25210389", "nama": "Bagas Tresna Nanda", "jurusan": "RPL", "kelas": "XII RPL 5"},
    {"nis": "25210390", "nama": "Khaidar Ali", "jurusan": "RPL", "kelas": "XI RPL 4"},
    {"nis": "25210391", "nama": "Muhammad Rizki Ramadhan", "jurusan": "RPL", "kelas": "XI RPL 4"},
    {"nis": "25210392", "nama": "Aji Ibram", "jurusan": "RPL", "kelas": "XI RPL 4"},
    {"nis": "25210393", "nama": "Desita Ayu Anggraeni", "jurusan": "RPL", "kelas": "X RPL 4"},
    {"nis": "25210394", "nama": "Dinda Kamila", "jurusan": "RPL", "kelas": "X RPL 4"},
]

# 1. Ensure students are added
existing_siswa = {s["nis"]: s for s in list_siswa()}
for data in students_data:
    if data["nis"] not in existing_siswa:
        try:
            add_siswa(data["nis"], data["nama"], data["jurusan"], data["kelas"])
            print(f"Added student: {data['nama']}")
        except Exception as e:
            print(f"Skipped {data['nama']}: {e}")

all_students = list_siswa()
print(f"Total students in DB: {len(all_students)}")

# 2. Simulate Attendance over 5 Mondays
mondays = ["2026-07-06", "2026-07-13", "2026-07-20", "2026-07-27", "2026-08-03"]

# Distribution of statuses for 10 students across 5 weeks to match user example pattern
# Hadir, Izin, Sakit, Alpha mix
status_patterns = [
    ["HADIR", "HADIR", "HADIR", "HADIR", "HADIR"], # 5 Hadir
    ["HADIR", "HADIR", "HADIR", "HADIR", "HADIR"], # 5 Hadir
    ["HADIR", "HADIR", "HADIR", "HADIR", "IZIN"],  # 4 Hadir, 1 Izin
    ["HADIR", "HADIR", "HADIR", "ALPHA", "HADIR"], # 4 Hadir, 1 Alpha
    ["HADIR", "SAKIT", "HADIR", "HADIR", "HADIR"], # 4 Hadir, 1 Sakit
    ["HADIR", "HADIR", "IZIN", "SAKIT", "HADIR"],  # 3 Hadir, 1 Izin, 1 Sakit
    ["HADIR", "HADIR", "ALPHA", "ALPHA", "HADIR"], # 3 Hadir, 2 Alpha
    ["IZIN", "IZIN", "HADIR", "HADIR", "HADIR"],   # 3 Hadir, 2 Izin
    ["SAKIT", "HADIR", "IZIN", "ALPHA", "HADIR"],  # 2 Hadir, 1 Izin, 1 Sakit, 1 Alpha
    ["HADIR", "ALPHA", "IZIN", "IZIN", "HADIR"],   # 2 Hadir, 2 Izin, 1 Alpha
]

for idx, student in enumerate(all_students[:10]):
    pattern = status_patterns[idx % len(status_patterns)]
    for m_idx, monday in enumerate(mondays):
        st = pattern[m_idx]
        set_manual_status(student["id"], st, monday)

print("✅ Attendance simulation populated successfully!")

# 3. Fetch Rekap Akumulasi
rekap = get_rekap_akumulasi_siswa()
print("\n--- REKAPITULASI AKUMULASI ABSENSI SISWA ---")
print(f"{'No':<4} | {'Nama Siswa':<30} | {'Kelas':<10} | {'H':<3} | {'I':<3} | {'S':<3} | {'A':<3} | {'Total'}")
print("-" * 75)
for r in rekap:
    print(f"{r['no']:<4} | {r['nama']:<30} | {r['kelas']:<10} | {r['hadir']:<3} | {r['izin']:<3} | {r['sakit']:<3} | {r['alpha']:<3} | {r['total_pertemuan']}")

# 4. Generate & Save Excel
excel_data = export_rekap_excel().getvalue()
excel_path = os.path.join(os.getcwd(), "rekap_akumulasi_10_siswa.xlsx")
with open(excel_path, "wb") as f:
    f.write(excel_data)

print(f"\n✅ Exported Excel saved to: {excel_path} ({len(excel_data)} bytes)")
