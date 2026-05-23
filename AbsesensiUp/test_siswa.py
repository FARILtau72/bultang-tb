"""Quick siswa login test."""
import requests, re

BASE = "http://127.0.0.1:8080"

# Get student data via admin
admin = requests.Session()
admin.post(f"{BASE}/login", data={"login_type": "admin", "username": "admin", "password": "admin123"})
r = admin.get(f"{BASE}/siswa")

# Parse NIS and Nama from table (NIS is in <td>, Nama in <td class="fw-semibold">)
rows = re.findall(r'<td>(\d+)</td>\s*<td class="fw-semibold">(.+?)</td>', r.text)
print(f"Students found: {len(rows)}")

if rows:
    nis, nama = rows[0]
    print(f"Testing with: {nama} (NIS: {nis})")
    
    # Login as siswa
    siswa = requests.Session()
    r = siswa.post(f"{BASE}/login", data={"login_type": "siswa", "nama": nama, "nis": nis}, allow_redirects=False)
    print(f"  Login: {r.status_code} -> {r.headers.get('Location', 'no redirect')}")
    
    # Access dashboard
    r = siswa.get(f"{BASE}/siswa/dashboard")
    print(f"  Dashboard: {r.status_code}")
    print(f"  Shows name: {nama in r.text}")
    print(f"  Shows NIS: {nis in r.text}")
    
    # Check QR status (not Monday)
    has_qr_unavailable = "belum tersedia" in r.text.lower()
    print(f"  QR unavailable msg (not Mon): {has_qr_unavailable}")
    
    # Try to redeem token (should fail - not Monday)
    r = siswa.post(f"{BASE}/siswa/redeem-token", json={"token": "SEN-TEST"})
    print(f"  Token redeem (not Mon): {r.status_code} -> {r.json().get('message', '')[:60]}")
    
    # RBAC: siswa blocked from admin pages
    for path in ["/dashboard", "/admin/absensi", "/siswa"]:
        r = siswa.get(f"{BASE}{path}", allow_redirects=False)
        status = "PASS" if r.status_code == 302 else "FAIL"
        print(f"  {status} Siswa blocked from {path} ({r.status_code})")
else:
    print("No students in database.")
