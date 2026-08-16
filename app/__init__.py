from datetime import timedelta, datetime
from pathlib import Path

from flask import Flask, send_from_directory

from app.core.config import BARCODE_FOLDER, REMEMBER_COOKIE_DAYS, SECRET_KEY, format_tanggal_display, format_waktu_display
from app.core.models import initialize_database
from app.routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.secret_key = SECRET_KEY
    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=REMEMBER_COOKIE_DAYS)

    # Initialize Flask-Login
    from flask_login import LoginManager
    from app.services.auth_service import load_user

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"
    login_manager.login_message = "Silakan login terlebih dahulu."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def _load_user(user_id):
        return load_user(user_id)

    initialize_database()
    register_blueprints(app)

    @app.context_processor
    def inject_helpers():
        return {"now": datetime.now}

    # Add Jinja filters for datetime formatting
    @app.template_filter('format_tanggal')
    def filter_format_tanggal(tanggal_str):
        return format_tanggal_display(tanggal_str)

    @app.template_filter('format_waktu')
    def filter_format_waktu(waktu_str):
        return format_waktu_display(waktu_str)

    # Custom route for barcodes so they work on Vercel ephemeral /tmp
    @app.route("/static/barcodes/<path:filename>")
    def barcodes(filename):
        import qrcode as qr_lib

        # Ensure barcodes folder exists
        BARCODE_FOLDER.mkdir(parents=True, exist_ok=True)

        file_path = BARCODE_FOLDER / filename
        if file_path.exists():
            return send_from_directory(str(BARCODE_FOLDER), filename)

        # Fallback to repo static/barcodes
        fallback = Path(__file__).resolve().parent / "static" / "barcodes"
        fallback_path = fallback / filename
        if fallback_path.exists():
            return send_from_directory(str(fallback), filename)

        # Auto-generate QR image if file doesn't exist but kode_qr is valid
        kode_qr = filename.replace(".png", "")
        if kode_qr.startswith("SISWA-"):
            qr_obj = qr_lib.QRCode(
                version=1,
                error_correction=qr_lib.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr_obj.add_data(kode_qr)
            qr_obj.make(fit=True)
            img = qr_obj.make_image(fill_color="black", back_color="white")
            img.save(str(file_path))
            return send_from_directory(str(BARCODE_FOLDER), filename)

        return "QR not found", 404

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
