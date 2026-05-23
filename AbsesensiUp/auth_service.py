"""
Authentication service - User model, login verification, and RBAC decorators.
"""

from functools import wraps

from flask import redirect, url_for, flash
from flask_login import UserMixin, current_user
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from config import ADMIN_USERNAME, ADMIN_PASSWORD
from db import get_engine


class User(UserMixin):
    """
    Unified user model for flask-login.
    
    ID format:
      - Siswa: "siswa:<siswa_id>"
      - Admin: "admin:<username>"
    """

    def __init__(self, user_id: str, role: str, data: dict):
        self._id = user_id
        self.role = role
        self.data = data

    def get_id(self) -> str:
        return self._id

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    @property
    def is_siswa(self) -> bool:
        return self.role == "siswa"

    @property
    def nama(self) -> str:
        return self.data.get("nama", "")

    @property
    def siswa_id(self) -> int | None:
        return self.data.get("id") if self.is_siswa else None


def load_user(user_id: str) -> User | None:
    """
    Flask-login user_loader callback.
    Reconstructs User object from stored session ID.
    """
    if not user_id:
        return None

    parts = user_id.split(":", 1)
    if len(parts) != 2:
        return None

    role, identifier = parts

    if role == "admin":
        if identifier == ADMIN_USERNAME:
            return User(
                user_id=user_id,
                role="admin",
                data={"username": ADMIN_USERNAME, "nama": "Administrator"},
            )
        return None

    if role == "siswa":
        try:
            siswa_id = int(identifier)
        except (ValueError, TypeError):
            return None

        engine = get_engine()
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT id, nis, nama, jurusan, kelas, kode_qr
                    FROM siswa
                    WHERE id = :siswa_id
                    """
                ),
                {"siswa_id": siswa_id},
            ).mappings().first()

        if not row:
            return None

        return User(
            user_id=user_id,
            role="siswa",
            data=dict(row),
        )

    return None


def authenticate_siswa(nama: str, nis: str) -> User | None:
    """
    Authenticate a student by name and NIS.
    
    Args:
        nama: Student name (case-insensitive match)
        nis: Student ID number (exact match)
        
    Returns:
        User object if authenticated, None otherwise
    """
    nama_clean = nama.strip()
    nis_clean = nis.strip()

    if not nama_clean or not nis_clean:
        return None

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id, nis, nama, jurusan, kelas, kode_qr
                FROM siswa
                WHERE nis = :nis
                """
            ),
            {"nis": nis_clean},
        ).mappings().first()

    if not row:
        return None

    # Case-insensitive name comparison
    if row["nama"].strip().lower() != nama_clean.lower():
        return None

    return User(
        user_id=f"siswa:{row['id']}",
        role="siswa",
        data=dict(row),
    )


def authenticate_admin(username: str, password: str) -> User | None:
    """
    Authenticate admin by username and password.
    
    Supports both hashed (werkzeug/pbkdf2/scrypt) and plaintext passwords in .env.
    To use a hashed password, set ADMIN_PASSWORD in .env to the output of:
        python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_password'))"
    """
    if username.strip() != ADMIN_USERNAME:
        return None

    # Support hashed password (starts with pbkdf2: or scrypt:)
    if ADMIN_PASSWORD.startswith(("pbkdf2:", "scrypt:")):
        password_valid = check_password_hash(ADMIN_PASSWORD, password)
    else:
        # Plaintext comparison (backward compatible)
        password_valid = password == ADMIN_PASSWORD

    if password_valid:
        return User(
            user_id=f"admin:{ADMIN_USERNAME}",
            role="admin",
            data={"username": ADMIN_USERNAME, "nama": "Administrator"},
        )
    return None


def admin_required(f):
    """Decorator: require admin role. Redirects to login if not authenticated or not admin."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login_page"))
        if not current_user.is_admin:
            flash("Akses ditolak. Halaman ini hanya untuk admin.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)

    return decorated_function


def siswa_required(f):
    """Decorator: require siswa role. Redirects to login if not authenticated or not siswa."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login_page"))
        if not current_user.is_siswa:
            flash("Akses ditolak. Halaman ini hanya untuk siswa.", "error")
            return redirect(url_for("auth.login_page"))
        return f(*args, **kwargs)

    return decorated_function
