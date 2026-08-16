from flask import Blueprint, render_template
from flask_login import current_user

from app.services.auth_service import siswa_required
from app.core.utils import get_now_wib


siswa_dash_bp = Blueprint("siswa_dash", __name__)


@siswa_dash_bp.route("/siswa/dashboard")
@siswa_required
def siswa_dashboard():
    now = get_now_wib()
    is_monday = now.weekday() == 0  # 0 = Monday

    siswa_data = current_user.data

    return render_template(
        "siswa_dashboard.html",
        siswa=siswa_data,
        is_monday=is_monday,
    )
