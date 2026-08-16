"""
Monday Token service - Generate, validate, and redeem weekly tokens.

Each Monday, admin generates a single token (e.g. SEN-A7X3).
All students use the same token to unlock their QR code for that day.
"""

import secrets
import string

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.db import get_engine
from app.core.utils import get_now_wib, get_today_str


def _generate_token_code() -> str:
    """Generate a random token like SEN-A7X3."""
    chars = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(chars) for _ in range(4))
    return f"SEN-{code}"


def generate_saturday_token(tanggal: str | None = None) -> dict:
    """
    Generate a new token for a specific Monday.
    
    Args:
        tanggal: Date string (YYYY-MM-DD). Defaults to today.
        
    Returns:
        Dict with token info or error message
    """
    tanggal = tanggal or get_today_str()
    token_code = _generate_token_code()
    now_str = get_now_wib().strftime("%Y-%m-%d %H:%M:%S")

    engine = get_engine()
    try:
        with engine.begin() as conn:
            # Check if token already exists for this date
            existing = conn.execute(
                text("SELECT token FROM saturday_token WHERE tanggal = :tanggal"),
                {"tanggal": tanggal},
            ).mappings().first()

            if existing:
                # Update existing token
                conn.execute(
                    text(
                        """
                        UPDATE saturday_token 
                        SET token = :token, created_at = :created_at 
                        WHERE tanggal = :tanggal
                        """
                    ),
                    {"token": token_code, "created_at": now_str, "tanggal": tanggal},
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO saturday_token (token, tanggal, created_at)
                        VALUES (:token, :tanggal, :created_at)
                        """
                    ),
                    {"token": token_code, "tanggal": tanggal, "created_at": now_str},
                )

        return {
            "status": "success",
            "token": token_code,
            "tanggal": tanggal,
            "message": f"Token {token_code} berhasil di-generate untuk {tanggal}.",
        }
    except IntegrityError:
        return {"status": "error", "message": "Gagal membuat token."}


def get_today_token() -> dict | None:
    """
    Get the token for today (if it exists).
    
    Returns:
        Dict with token info or None
    """
    today = get_today_str()
    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT token, tanggal, created_at FROM saturday_token WHERE tanggal = :tanggal"),
            {"tanggal": today},
        ).mappings().first()

    if not row:
        return None

    return dict(row)


def get_token_for_date(tanggal: str) -> dict | None:
    """Get token for a specific date."""
    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT token, tanggal, created_at FROM saturday_token WHERE tanggal = :tanggal"),
            {"tanggal": tanggal},
        ).mappings().first()

    return dict(row) if row else None


def validate_token(token_input: str, tanggal: str | None = None) -> bool:
    """
    Validate a token against the stored token for the given date.
    
    Args:
        token_input: Token string to validate
        tanggal: Date to check (defaults to today)
        
    Returns:
        True if token is valid
    """
    tanggal = tanggal or get_today_str()
    token_clean = token_input.strip().upper()

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT token FROM saturday_token WHERE tanggal = :tanggal"),
            {"tanggal": tanggal},
        ).mappings().first()

    if not row:
        return False

    return row["token"] == token_clean


def redeem_token(siswa_id: int, tanggal: str | None = None) -> bool:
    """
    Record that a student has redeemed the token for the given date.
    
    Args:
        siswa_id: Student ID
        tanggal: Date (defaults to today)
        
    Returns:
        True if redemption was recorded, False if already redeemed
    """
    tanggal = tanggal or get_today_str()
    now_str = get_now_wib().strftime("%Y-%m-%d %H:%M:%S")

    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO token_redemption (siswa_id, tanggal, redeemed_at)
                    VALUES (:siswa_id, :tanggal, :redeemed_at)
                    """
                ),
                {"siswa_id": siswa_id, "tanggal": tanggal, "redeemed_at": now_str},
            )
        return True
    except IntegrityError:
        # Already redeemed
        return False


def has_redeemed_token(siswa_id: int, tanggal: str | None = None) -> bool:
    """
    Check if a student has already redeemed the token for the given date.
    """
    tanggal = tanggal or get_today_str()

    engine = get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT id FROM token_redemption 
                WHERE siswa_id = :siswa_id AND tanggal = :tanggal
                """
            ),
            {"siswa_id": siswa_id, "tanggal": tanggal},
        ).mappings().first()

    return row is not None
