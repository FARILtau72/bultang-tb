"""
Models module - Aggregate module for backward compatibility.

This module re-exports all functions from the refactored service modules:
- db: Database initialization and connection management
- siswa_service: Student management business logic
- absensi_service: Attendance management business logic
- utils: Utility functions
- token_service: Monday token management

For new code, consider importing directly from the specific modules.
"""

# Database functions
from app.core.db import (
    get_connection,
    get_engine,
    initialize_database,
    init_db,
    using_tidb,
)

# Siswa (Student) functions
from app.services.siswa_service import (
    add_siswa,
    delete_siswa,
    edit_siswa,
    get_kelas_options,
    get_siswa_by_id,
    list_siswa,
    regenerate_qr_siswa,
)

# Absensi (Attendance) functions
from app.services.absensi_service import (
    export_rekap_excel,
    get_dashboard_metrics,
    get_recent_absensi,
    get_rekap_absensi,
    get_rekap_akumulasi_siswa,
    get_rekap_stats_per_kelas,
    get_today_attendance_map,
    get_today_jurusan_summary,
    process_scan_qr,
    set_manual_status,
)

# Token functions
from app.services.token_service import (
    generate_saturday_token,
    get_today_token,
    get_token_for_date,
    has_redeemed_token,
    redeem_token,
    validate_token,
)

# Utility functions
from app.core.utils import (
    format_tanggal_display,
    format_waktu_display,
    get_now_time_str,
    get_now_wib,
    get_today_str,
)

__all__ = [
    # Database
    "get_connection",
    "get_engine",
    "initialize_database",
    "init_db",
    "using_tidb",
    # Siswa
    "add_siswa",
    "delete_siswa",
    "edit_siswa",
    "get_kelas_options",
    "get_siswa_by_id",
    "list_siswa",
    "regenerate_qr_siswa",
    # Absensi
    "export_rekap_excel",
    "get_dashboard_metrics",
    "get_recent_absensi",
    "get_rekap_absensi",
    "get_rekap_stats_per_kelas",
    "get_today_attendance_map",
    "get_today_jurusan_summary",
    "process_scan_qr",
    "set_manual_status",
    # Token
    "generate_saturday_token",
    "get_today_token",
    "get_token_for_date",
    "has_redeemed_token",
    "redeem_token",
    "validate_token",
    # Utils
    "format_tanggal_display",
    "format_waktu_display",
    "get_now_time_str",
    "get_now_wib",
    "get_today_str",
]
