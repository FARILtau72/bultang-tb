from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

from auth_service import admin_required
from models import get_dashboard_metrics, get_recent_absensi, get_today_jurusan_summary


dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def landing_page():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("siswa_dash.siswa_dashboard"))
    return redirect(url_for("auth.login_page"))


@dashboard_bp.route("/dashboard")
@admin_required
def index():
    metrics = get_dashboard_metrics()
    jurusan_summary = get_today_jurusan_summary()
    recent_absensi = get_recent_absensi(limit=10)

    chart_labels = [item["jurusan"] for item in jurusan_summary]
    chart_hadir = [item["hadir_count"] for item in jurusan_summary]

    return render_template(
        "dashboard.html",
        metrics=metrics,
        jurusan_summary=jurusan_summary,
        chart_labels=chart_labels,
        chart_hadir=chart_hadir,
        recent_absensi=recent_absensi,
    )
