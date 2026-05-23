from flask import Blueprint, render_template, request, jsonify

from auth_service import admin_required
from config import JURUSAN, STATUS_OPTIONS
from models import (
    get_kelas_options,
    list_siswa,
    get_today_attendance_map,
    set_manual_status,
    generate_saturday_token,
    get_today_token,
)
from utils import get_now_wib, get_today_str


admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/absensi")
@admin_required
def admin_absensi():
    jurusan = (request.args.get("jurusan") or "").upper().strip()
    kelas = (request.args.get("kelas") or "").upper().strip()

    jurusan_filter = jurusan if jurusan in JURUSAN else None
    kelas_filter = kelas if kelas else None

    data_siswa = list_siswa(jurusan_filter, kelas_filter)
    attendance_map = get_today_attendance_map()
    kelas_options = get_kelas_options(jurusan_filter)

    now = get_now_wib()
    is_monday = now.weekday() == 0
    today_token = get_today_token()

    # Compute stats server-side for clean template rendering
    stats = {"total": len(data_siswa), "hadir": 0, "sakit": 0, "izin": 0, "alpha": 0, "belum": 0}
    for s in data_siswa:
        info = attendance_map.get(s["id"])
        if info:
            st = info["status"]
            if st == "HADIR":
                stats["hadir"] += 1
            elif st == "SAKIT":
                stats["sakit"] += 1
            elif st == "IZIN":
                stats["izin"] += 1
            elif st == "ALPHA":
                stats["alpha"] += 1
        else:
            stats["belum"] += 1

    return render_template(
        "admin_absensi.html",
        siswa_list=data_siswa,
        attendance_map=attendance_map,
        jurusan_options=JURUSAN,
        kelas_options=kelas_options,
        status_options=STATUS_OPTIONS,
        filters={"jurusan": jurusan_filter or "", "kelas": kelas_filter or ""},
        is_saturday=is_monday,
        today_token=today_token,
        tanggal=get_today_str(),
        stats=stats,
    )


@admin_bp.route("/api/admin/set-status", methods=["POST"])
@admin_required
def api_set_status():
    payload = request.get_json(silent=True) or {}
    siswa_id = payload.get("siswa_id")
    status = payload.get("status", "").strip().upper()

    if not siswa_id:
        return jsonify({"status": "error", "message": "siswa_id diperlukan."}), 400

    if status not in STATUS_OPTIONS:
        return jsonify({"status": "error", "message": f"Status '{status}' tidak valid."}), 400

    result = set_manual_status(int(siswa_id), status)

    if result["status"] == "error":
        return jsonify(result), 400

    return jsonify(result), 200


@admin_bp.route("/api/admin/generate-token", methods=["POST"])
@admin_required
def api_generate_token():
    result = generate_saturday_token()
    if result["status"] == "error":
        return jsonify(result), 500

    return jsonify(result), 200


@admin_bp.route("/api/admin/today-token")
@admin_required
def api_today_token():
    token = get_today_token()
    if not token:
        return jsonify({"status": "empty", "message": "Belum ada token untuk hari ini."}), 200

    return jsonify({"status": "success", "token": token}), 200
