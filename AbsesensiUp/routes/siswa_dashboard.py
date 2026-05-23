from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user

from auth_service import siswa_required
from token_service import validate_token, redeem_token, has_redeemed_token, get_today_token
from utils import get_now_wib


siswa_dash_bp = Blueprint("siswa_dash", __name__)


@siswa_dash_bp.route("/siswa/dashboard")
@siswa_required
def siswa_dashboard():
    now = get_now_wib()
    is_monday = now.weekday() == 0  # 0 = Monday

    siswa_data = current_user.data
    token_redeemed = False
    today_token_exists = False

    if is_monday:
        token_info = get_today_token()
        today_token_exists = token_info is not None
        token_redeemed = has_redeemed_token(current_user.siswa_id)

    return render_template(
        "siswa_dashboard.html",
        siswa=siswa_data,
        is_monday=is_monday,
        token_redeemed=token_redeemed,
        today_token_exists=today_token_exists,
    )


@siswa_dash_bp.route("/siswa/redeem-token", methods=["POST"])
@siswa_required
def redeem_token_route():
    now = get_now_wib()
    is_monday = now.weekday() == 0

    if not is_monday:
        return jsonify({"status": "error", "message": "Token hanya bisa ditukar pada hari Senin."}), 400

    payload = request.get_json(silent=True) or {}
    token_input = (payload.get("token") or "").strip()

    if not token_input:
        return jsonify({"status": "error", "message": "Token tidak boleh kosong."}), 400

    # Check if already redeemed
    if has_redeemed_token(current_user.siswa_id):
        return jsonify({"status": "already", "message": "Anda sudah menukar token hari ini."}), 200

    # Validate token
    if not validate_token(token_input):
        return jsonify({"status": "error", "message": "Token salah. Periksa kembali token Anda."}), 400

    # Redeem
    redeem_token(current_user.siswa_id)

    return jsonify({
        "status": "success",
        "message": "Token berhasil ditukar! QR Code Anda sudah tersedia.",
    }), 200
