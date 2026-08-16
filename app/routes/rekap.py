from datetime import datetime

from flask import Blueprint, render_template, request, send_file

from app.services.auth_service import admin_required
from app.core.config import JURUSAN, STATUS_OPTIONS
from app.core.models import (
    export_rekap_excel,
    get_kelas_options,
    get_rekap_akumulasi_siswa,
)
from app.core.utils import format_tanggal_display


rekap_bp = Blueprint("rekap", __name__)


def _read_filters() -> dict:
    return {
        "start_date": (request.args.get("start_date") or "").strip(),
        "end_date": (request.args.get("end_date") or "").strip(),
        "jurusan": (request.args.get("jurusan") or "").upper().strip(),
        "kelas": (request.args.get("kelas") or "").upper().strip(),
    }


@rekap_bp.route("/rekap")
@admin_required
def rekap_page():
    filters = _read_filters()

    jurusan_filter = filters["jurusan"] if filters["jurusan"] in JURUSAN else None
    kelas_filter = filters["kelas"] if filters["kelas"] else None

    rows = get_rekap_akumulasi_siswa(
        start_date=filters["start_date"] or None,
        end_date=filters["end_date"] or None,
        jurusan=jurusan_filter,
        kelas=kelas_filter,
    )

    # Compute total summary
    totals = {
        "hadir": sum(int(r["hadir"]) for r in rows),
        "izin": sum(int(r["izin"]) for r in rows),
        "sakit": sum(int(r["sakit"]) for r in rows),
        "alpha": sum(int(r["alpha"]) for r in rows),
        "total_pertemuan": sum(int(r["total_pertemuan"]) for r in rows),
    }

    start = filters["start_date"]
    end = filters["end_date"]
    if start and end:
        periode_str = f"{format_tanggal_display(start)} - {format_tanggal_display(end)}"
    elif start:
        periode_str = f"Mulai {format_tanggal_display(start)}"
    elif end:
        periode_str = f"Hingga {format_tanggal_display(end)}"
    else:
        periode_str = "Semua Periode"

    return render_template(
        "rekap.html",
        rows=rows,
        totals=totals,
        periode_str=periode_str,
        jurusan_options=JURUSAN,
        kelas_options=get_kelas_options(jurusan_filter),
        filters={
            "start_date": filters["start_date"],
            "end_date": filters["end_date"],
            "jurusan": jurusan_filter or "",
            "kelas": kelas_filter or "",
        },
    )


@rekap_bp.route("/rekap/export")
@admin_required
def rekap_export_excel_route():
    filters = _read_filters()

    jurusan_filter = filters["jurusan"] if filters["jurusan"] in JURUSAN else None
    kelas_filter = filters["kelas"] if filters["kelas"] else None

    excel_output = export_rekap_excel(
        start_date=filters["start_date"] or None,
        end_date=filters["end_date"] or None,
        jurusan=jurusan_filter,
        kelas=kelas_filter,
    )

    file_name = f"rekap_akumulasi_absensi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(excel_output, as_attachment=True, download_name=file_name)
