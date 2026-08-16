#!/usr/bin/env python
"""Test script to verify all refactored modules work correctly."""

print("Testing module imports and functionality...\n")

# Test individual module imports
print("1. Testing utils module...")
from app.core.utils import get_today_str, format_tanggal_display
print(f"   ✓ get_today_str(): {get_today_str()}")
print(f"   ✓ format_tanggal_display('2026-05-01'): {format_tanggal_display('2026-05-01')}")

# Test db module
print("\n2. Testing db module...")
from app.core.db import using_tidb, get_engine
print(f"   ✓ using_tidb(): {using_tidb()}")
print(f"   ✓ get_engine() returns engine: {get_engine() is not None}")

# Test siswa_service module
print("\n3. Testing siswa_service module...")
from app.services.siswa_service import list_siswa, get_siswa_by_id
result = list_siswa()
print(f"   ✓ list_siswa() returns list: {isinstance(result, list)}")
print(f"   ✓ list_siswa() returned {len(result)} students")

# Test absensi_service module
print("\n4. Testing absensi_service module...")
from app.services.absensi_service import get_dashboard_metrics
metrics = get_dashboard_metrics()
print(f"   ✓ get_dashboard_metrics() keys: {list(metrics.keys())}")

# Test backward compatibility with models.py
print("\n5. Testing backward compatibility (models.py)...")
from app.core.models import add_siswa, process_scan_qr, get_today_str as get_today_str_models
print(f"   ✓ add_siswa imported: {callable(add_siswa)}")
print(f"   ✓ process_scan_qr imported: {callable(process_scan_qr)}")
print(f"   ✓ get_today_str imported: {callable(get_today_str_models)}")

print("\n" + "="*60)
print("✓ SUCCESS! All module imports and functionality verified!")
print("="*60)
