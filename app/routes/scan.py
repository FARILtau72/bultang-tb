from flask import Blueprint, jsonify, render_template, request

from app.services.auth_service import admin_required
from app.core.models import process_scan_qr


scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/scan")
@admin_required
def scan_page():
    return render_template("scan.html")


@scan_bp.route("/api/process_scan", methods=["POST"])
@admin_required
def process_scan():
    payload = request.get_json(silent=True) or {}
    code = (payload.get("code") or "").strip()
    status = (payload.get("status") or "HADIR").strip().upper()

    if not code:
        return jsonify({"status": "error", "message": "Kode QR tidak terbaca."}), 400

    result = process_scan_qr(code, status=status)

    if result["status"] == "error":
        return jsonify(result), 404

    return jsonify(result), 200
