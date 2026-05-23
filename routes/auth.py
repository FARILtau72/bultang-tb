from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user

from auth_service import authenticate_siswa, authenticate_admin


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():
    # If already logged in, redirect to appropriate dashboard
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for("dashboard.index"))
        return redirect(url_for("siswa_dash.siswa_dashboard"))

    error_message = None
    active_tab = request.form.get("login_type", "siswa")

    if request.method == "POST":
        login_type = request.form.get("login_type", "siswa")
        active_tab = login_type

        if login_type == "siswa":
            nama = request.form.get("nama", "").strip()
            nis = request.form.get("nis", "").strip()

            if not nama or not nis:
                error_message = "Nama dan NIS wajib diisi."
            else:
                user = authenticate_siswa(nama, nis)
                if user:
                    login_user(user, remember=True)
                    return redirect(url_for("siswa_dash.siswa_dashboard"))
                else:
                    error_message = "Nama atau NIS salah. Pastikan data sesuai dengan yang terdaftar."

        elif login_type == "admin":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if not username or not password:
                error_message = "Username dan password wajib diisi."
            else:
                user = authenticate_admin(username, password)
                if user:
                    login_user(user, remember=True)
                    return redirect(url_for("dashboard.index"))
                else:
                    error_message = "Username atau password salah."

    return render_template("login.html", error_message=error_message, active_tab=active_tab)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Anda telah keluar dari sistem.", "info")
    return redirect(url_for("auth.login_page"))
