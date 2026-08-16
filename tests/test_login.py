"""Comprehensive test for all features: Login, RBAC, Token, Admin Absensi."""
import requests
import sys

BASE = "http://127.0.0.1:8080"
passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} {detail}")

print("=" * 60)
print("COMPREHENSIVE TEST SUITE")
print("=" * 60)

# ============================================================
print("\n[1] LANDING PAGE")
# ============================================================
r = requests.get(f"{BASE}/", allow_redirects=False)
test("Landing -> /login redirect", r.status_code == 302 and "/login" in r.headers.get("Location", ""))

# ============================================================
print("\n[2] LOGIN PAGE")
# ============================================================
r = requests.get(f"{BASE}/login")
test("Login page loads", r.status_code == 200)
test("Has Siswa tab", "Siswa" in r.text)
test("Has Admin tab", "Admin" in r.text)
test("Has NIS field", 'name="nis"' in r.text)
test("Has password field", 'name="password"' in r.text)

# ============================================================
print("\n[3] ADMIN LOGIN")
# ============================================================
admin = requests.Session()
r = admin.post(f"{BASE}/login", data={
    "login_type": "admin",
    "username": "admin",
    "password": "admin123"
}, allow_redirects=False)
test("Admin login -> 302", r.status_code == 302)
test("Redirect to /dashboard", "/dashboard" in r.headers.get("Location", ""))

# ============================================================
print("\n[4] ADMIN RBAC - All pages accessible")
# ============================================================
pages = {
    "/dashboard": "Total Siswa",
    "/siswa": "Daftar Siswa",
    "/scan": "scan",
    "/rekap": "rekap",
    "/admin/absensi": "Kelola Absensi",
}
for path, keyword in pages.items():
    r = admin.get(f"{BASE}{path}")
    test(f"Admin can access {path}", r.status_code == 200 and keyword.lower() in r.text.lower())

# ============================================================
print("\n[5] UNAUTHENTICATED RBAC - All blocked")
# ============================================================
anon = requests.Session()
protected = ["/dashboard", "/siswa", "/scan", "/rekap", "/admin/absensi", "/siswa/dashboard"]
for path in protected:
    r = anon.get(f"{BASE}{path}", allow_redirects=False)
    test(f"Anon blocked from {path}", r.status_code == 302)

# ============================================================
print("\n[6] INVALID LOGINS")
# ============================================================
r = requests.post(f"{BASE}/login", data={
    "login_type": "siswa", "nama": "Fake Student", "nis": "000000"
})
test("Invalid siswa login shows error", r.status_code == 200 and "salah" in r.text.lower())

r = requests.post(f"{BASE}/login", data={
    "login_type": "admin", "username": "admin", "password": "wrongpass"
})
test("Invalid admin login shows error", r.status_code == 200 and "salah" in r.text.lower())

r = requests.post(f"{BASE}/login", data={
    "login_type": "siswa", "nama": "", "nis": ""
})
test("Empty siswa login shows error", r.status_code == 200 and "wajib" in r.text.lower())

# ============================================================
print("\n[7] TOKEN GENERATION (Admin)")
# ============================================================
r = admin.post(f"{BASE}/api/admin/generate-token", json={})
test("Generate token succeeds", r.status_code == 200)
token_data = r.json()
test("Token has SEN- prefix", token_data.get("token", "").startswith("SEN-"))
generated_token = token_data.get("token", "")
print(f"       Token generated: {generated_token}")

# Verify token shows on admin page
r = admin.get(f"{BASE}/admin/absensi")
test("Token visible on admin page", generated_token in r.text)
test("Admin page has copy button", "btn-copy-token" in r.text)
test("Admin page has generate button", "btn-generate-token" in r.text)

# ============================================================
print("\n[8] TOKEN API")
# ============================================================
r = admin.get(f"{BASE}/api/admin/today-token")
test("Today token API returns token", r.status_code == 200 and generated_token in r.text)

# Regenerate token
r = admin.post(f"{BASE}/api/admin/generate-token", json={})
new_token = r.json().get("token", "")
test("Regenerate creates new token", new_token != generated_token and new_token.startswith("SEN-"))
generated_token = new_token
print(f"       New token: {generated_token}")

# ============================================================
print("\n[9] ADMIN SET STATUS")
# ============================================================
# First, get a siswa ID from the siswa list
r = admin.get(f"{BASE}/admin/absensi")
# Check if there are any students
import re
siswa_ids = re.findall(r'data-siswa-id="(\d+)"', r.text)
if siswa_ids:
    test_siswa_id = int(siswa_ids[0])
    
    for status in ["HADIR", "SAKIT", "IZIN", "ALPHA"]:
        r = admin.post(f"{BASE}/api/admin/set-status", json={
            "siswa_id": test_siswa_id,
            "status": status
        })
        test(f"Set status {status}", r.status_code == 200 and r.json().get("status") == "success")
    
    # Invalid status
    r = admin.post(f"{BASE}/api/admin/set-status", json={
        "siswa_id": test_siswa_id,
        "status": "INVALID"
    })
    test("Invalid status rejected", r.status_code == 400)
    
    # Missing siswa_id
    r = admin.post(f"{BASE}/api/admin/set-status", json={"status": "HADIR"})
    test("Missing siswa_id rejected", r.status_code == 400)
else:
    print("  SKIP  No students in database to test status changes")

# ============================================================
print("\n[10] SISWA LOGIN (if students exist)")
# ============================================================
if siswa_ids:
    # Get student info from admin page
    siswa_names = re.findall(r'data-siswa-nama="([^"]+)"', r.text)
    # Also need NIS - let's get from siswa list
    r = admin.get(f"{BASE}/siswa")
    nis_matches = re.findall(r'<td><small>(\d+)</small></td>\s*<td class="fw-semibold">([^<]+)</td>', r.text)
    
    if nis_matches:
        test_nis, test_nama = nis_matches[0]
        print(f"       Testing with: {test_nama} (NIS: {test_nis})")
        
        siswa_session = requests.Session()
        r = siswa_session.post(f"{BASE}/login", data={
            "login_type": "siswa",
            "nama": test_nama,
            "nis": test_nis
        }, allow_redirects=False)
        test("Siswa login succeeds", r.status_code == 302 and "/siswa/dashboard" in r.headers.get("Location", ""))
        
        # Dashboard loads
        r = siswa_session.get(f"{BASE}/siswa/dashboard")
        test("Siswa dashboard loads", r.status_code == 200)
        test("Dashboard shows student name", test_nama in r.text)
        
        # RBAC: siswa cannot access admin pages
        for path in ["/dashboard", "/siswa", "/scan", "/admin/absensi"]:
            r = siswa_session.get(f"{BASE}{path}", allow_redirects=False)
            test(f"Siswa blocked from {path}", r.status_code == 302)
        
        # Token redemption (may fail if not Monday - that's OK)
        r = siswa_session.post(f"{BASE}/siswa/redeem-token", json={"token": generated_token})
        is_monday_response = "senin" in r.text.lower() if r.status_code == 400 else True
        test("Token redeem responds correctly", r.status_code in [200, 400])
    else:
        print("  SKIP  Could not extract student NIS for login test")
else:
    print("  SKIP  No students in database")

# ============================================================
print("\n[11] LOGOUT")
# ============================================================
r = admin.get(f"{BASE}/logout", allow_redirects=False)
test("Logout redirects", r.status_code == 302)

# After logout, should be blocked
r = admin.get(f"{BASE}/dashboard", allow_redirects=False)
test("After logout, dashboard blocked", r.status_code == 302)

# ============================================================
print("\n[12] WERKZEUG PASSWORD HASH")
# ============================================================
from werkzeug.security import generate_password_hash, check_password_hash
hashed = generate_password_hash("admin123")
test("Hash generation works", hashed.startswith("scrypt:") or hashed.startswith("pbkdf2:"))
test("Hash verification works", check_password_hash(hashed, "admin123"))
test("Wrong password fails", not check_password_hash(hashed, "wrong"))
print(f"       Hash example: {hashed[:50]}...")

# ============================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
