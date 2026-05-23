from app import app
client = app.test_client()
routes = ["/", "/dashboard", "/scan", "/siswa", "/rekap"]
for r in routes:
    try: print(f"{r}: {client.get(r).status_code}")
    except Exception as e: print(f"{r}: {e}")
rules = [str(x) for x in app.url_map.iter_rules()]
print(f"Dashboard in map: {any('/dashboard' in r for r in rules)}")
print(f"Root in map: {any(r.split()[0] == '/' for r in rules)}")
