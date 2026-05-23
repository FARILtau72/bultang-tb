from datetime import datetime
from io import BytesIO

import pandas as pd
from flask import Blueprint, render_template, request, send_file

from auth_service import admin_required
from config import JURUSAN, STATUS_OPTIONS
from models import get_kelas_options, get_rekap_absensi, get_rekap_stats_per_kelas


rekap_bp = Blueprint("rekap", __name__)


def _read_filters() -> dict:
    return {
        "start_date": (request.args.get("start_date") or "").strip(),
        "end_date": (request.args.get("end_date") or "").strip(),
        "jurusan": (request.args.get("jurusan") or "").upper().strip(),
        "kelas": (request.args.get("kelas") or "").upper().strip(),
        "status": (request.args.get("status") or "").upper().strip(),
    }


@rekap_bp.route("/rekap")
@admin_required
def rekap_page():
    filters = _read_filters()

    jurusan_filter = filters["jurusan"] if filters["jurusan"] in JURUSAN else None
    kelas_filter = filters["kelas"] if filters["kelas"] else None
    status_filter = filters["status"] if filters["status"] in STATUS_OPTIONS else None

    rows = get_rekap_absensi(
        start_date=filters["start_date"] or None,
        end_date=filters["end_date"] or None,
        jurusan=jurusan_filter,
        kelas=kelas_filter,
        status=status_filter,
    )
    kelas_stats = get_rekap_stats_per_kelas(
        start_date=filters["start_date"] or None,
        end_date=filters["end_date"] or None,
        jurusan=jurusan_filter,
        kelas=kelas_filter,
    )

    return render_template(
        "rekap.html",
        rows=rows,
        kelas_stats=kelas_stats,
        jurusan_options=JURUSAN,
        kelas_options=get_kelas_options(jurusan_filter),
        status_options=STATUS_OPTIONS,
        filters={
            "start_date": filters["start_date"],
            "end_date": filters["end_date"],
            "jurusan": jurusan_filter or "",
            "kelas": kelas_filter or "",
            "status": status_filter or "",
        },
    )


@rekap_bp.route("/rekap/export")
@admin_required
def rekap_export_excel():
    filters = _read_filters()

    jurusan_filter = filters["jurusan"] if filters["jurusan"] in JURUSAN else None
    kelas_filter = filters["kelas"] if filters["kelas"] else None
    status_filter = filters["status"] if filters["status"] in STATUS_OPTIONS else None

    rows = get_rekap_absensi(
        start_date=filters["start_date"] or None,
        end_date=filters["end_date"] or None,
        jurusan=jurusan_filter,
        kelas=kelas_filter,
        status=status_filter,
    )

    dataframe = pd.DataFrame(rows)
    if dataframe.empty:
        dataframe = pd.DataFrame(
            columns=["id", "nama", "kelas", "jurusan", "waktu", "tanggal", "status"]
        )

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Rekap Absensi")

    output.seek(0)
    file_name = f"rekap_absensi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(output, as_attachment=True, download_name=file_name)
