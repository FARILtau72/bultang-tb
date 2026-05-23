from flask import Flask


def register_blueprints(app: Flask) -> None:
    from .auth import auth_bp
    from .dashboard import dashboard_bp
    from .rekap import rekap_bp
    from .scan import scan_bp
    from .siswa import siswa_bp
    from .siswa_dashboard import siswa_dash_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(siswa_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(rekap_bp)
    app.register_blueprint(siswa_dash_bp)
    app.register_blueprint(admin_bp)
