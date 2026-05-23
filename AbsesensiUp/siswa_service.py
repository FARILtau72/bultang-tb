"""
Student (Siswa) management business logic.
"""

from pathlib import Path
from uuid import uuid4

import qrcode
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from config import BARCODE_FOLDER, JURUSAN, KELAS_LIST, kelas_by_jurusan
from db import get_engine


def get_kelas_options(jurusan: str | None = None) -> list[str]:
    """Get kelas options, optionally filtered by jurusan."""
    return kelas_by_jurusan(jurusan)


def _generate_qr_image(kode_qr: str) -> str:
    """
    Generate QR code image for a student.
    
    Args:
        kode_qr: QR code identifier
        
    Returns:
        Path to the saved QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(kode_qr)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    file_name = f"{kode_qr}.png"
    file_path = BARCODE_FOLDER / file_name
    img.save(file_path)

    return f"barcodes/{file_name}"


def _new_qr_code(nis: str) -> str:
    """Generate a new unique QR code identifier."""
    return f"SISWA-{nis}-{uuid4().hex[:8].upper()}"


def _row_to_siswa(row: dict) -> dict:
    """Convert database row to siswa dictionary."""
    return {
        "id": row["id"],
        "nis": row["nis"],
        "nama": row["nama"],
        "jurusan": row["jurusan"],
        "kelas": row["kelas"],
        "kode_qr": row["kode_qr"],
        "qr_image": f"barcodes/{row['kode_qr']}.png",
    }


def _validate_siswa(jurusan: str, kelas: str) -> None:
    """
    Validate student jurusan and kelas.
    
    Raises:
        ValueError: If validation fails
    """
    if jurusan not in JURUSAN:
        raise ValueError("Jurusan tidak valid.")

    if kelas not in KELAS_LIST:
        raise ValueError("Kelas tidak valid.")

    if kelas not in kelas_by_jurusan(jurusan):
        raise ValueError("Kelas tidak sesuai dengan jurusan.")


def add_siswa(nis: str, nama: str, jurusan: str, kelas: str) -> dict:
    """
    Add a new student to the database.
    
    Args:
        nis: Student ID number
        nama: Student name
        jurusan: Major/Department
        kelas: Class
        
    Returns:
        Dictionary with student data
        
    Raises:
        ValueError: If input is invalid or student already exists
    """
    nis_clean = nis.strip()
    nama_clean = nama.strip()
    jurusan_clean = jurusan.strip().upper()
    kelas_clean = kelas.strip().upper()

    if not nis_clean or not nama_clean:
        raise ValueError("NIS dan nama wajib diisi.")

    _validate_siswa(jurusan_clean, kelas_clean)

    kode_qr = _new_qr_code(nis_clean)
    engine = get_engine()

    try:
        with engine.begin() as conn:
            cur = conn.execute(
                text(
                    """
                    INSERT INTO siswa (nis, nama, jurusan, kelas, kode_qr)
                    VALUES (:nis, :nama, :jurusan, :kelas, :kode_qr)
                    """
                ),
                {
                    "nis": nis_clean,
                    "nama": nama_clean,
                    "jurusan": jurusan_clean,
                    "kelas": kelas_clean,
                    "kode_qr": kode_qr,
                },
            )
            siswa_id = int(cur.lastrowid)
        _generate_qr_image(kode_qr)
    except IntegrityError as exc:
        if "nis" in str(exc).lower():
            raise ValueError("NIS sudah terdaftar.") from exc
        raise ValueError("Gagal menyimpan data siswa.") from exc

    siswa = get_siswa_by_id(siswa_id)
    if not siswa:
        raise ValueError("Gagal memuat data siswa setelah disimpan.")
    return siswa


def get_siswa_by_id(siswa_id: int) -> dict | None:
    """
    Get student data by ID.
    
    Args:
        siswa_id: Student ID
        
    Returns:
        Student dictionary or None if not found
    """
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

    return _row_to_siswa(row) if row else None


def list_siswa(jurusan: str | None = None, kelas: str | None = None) -> list[dict]:
    """
    List students with optional filtering.
    
    Args:
        jurusan: Filter by major (optional)
        kelas: Filter by class (optional)
        
    Returns:
        List of student dictionaries
    """
    query = "SELECT id, nis, nama, jurusan, kelas, kode_qr FROM siswa WHERE 1=1"
    params: dict = {}

    if jurusan:
        query += " AND jurusan = :jurusan"
        params["jurusan"] = jurusan.upper()

    if kelas:
        query += " AND kelas = :kelas"
        params["kelas"] = kelas.upper()

    query += " ORDER BY id DESC"

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    return [_row_to_siswa(row) for row in rows]


def regenerate_qr_siswa(siswa_id: int) -> dict | None:
    """
    Regenerate QR code for a student.
    
    Args:
        siswa_id: Student ID
        
    Returns:
        Updated student dictionary or None if not found
    """
    siswa = get_siswa_by_id(siswa_id)
    if not siswa:
        return None

    old_qr_path = BARCODE_FOLDER / f"{siswa['kode_qr']}.png"
    if old_qr_path.exists():
        old_qr_path.unlink()

    new_kode_qr = _new_qr_code(siswa["nis"])
    engine = get_engine()

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE siswa SET kode_qr = :kode_qr WHERE id = :siswa_id"),
            {"kode_qr": new_kode_qr, "siswa_id": siswa_id},
        )

    _generate_qr_image(new_kode_qr)
    return get_siswa_by_id(siswa_id)


def edit_siswa(siswa_id: int, nis: str, nama: str, jurusan: str, kelas: str) -> dict:
    """
    Edit student data.
    
    Args:
        siswa_id: Student ID
        nis: New student ID number
        nama: New name
        jurusan: New major
        kelas: New class
        
    Returns:
        Updated student dictionary
        
    Raises:
        ValueError: If input is invalid or student not found
    """
    nis_clean = nis.strip()
    nama_clean = nama.strip()
    jurusan_clean = jurusan.strip().upper()
    kelas_clean = kelas.strip().upper()

    if not nis_clean or not nama_clean:
        raise ValueError("NIS dan nama wajib diisi.")

    _validate_siswa(jurusan_clean, kelas_clean)

    siswa = get_siswa_by_id(siswa_id)
    if not siswa:
        raise ValueError("Data siswa tidak ditemukan.")

    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    UPDATE siswa
                    SET nis = :nis, nama = :nama, jurusan = :jurusan, kelas = :kelas
                    WHERE id = :siswa_id
                    """
                ),
                {
                    "nis": nis_clean,
                    "nama": nama_clean,
                    "jurusan": jurusan_clean,
                    "kelas": kelas_clean,
                    "siswa_id": siswa_id,
                },
            )
    except IntegrityError as exc:
        if "nis" in str(exc).lower():
            raise ValueError("NIS sudah terdaftar.") from exc
        raise ValueError("Gagal mengubah data siswa.") from exc

    return get_siswa_by_id(siswa_id) or siswa


def delete_siswa(siswa_id: int) -> bool:
    """
    Delete a student and related records.
    
    Args:
        siswa_id: Student ID
        
    Returns:
        True if deleted, False if not found
        
    Raises:
        ValueError: If deletion fails
    """
    siswa = get_siswa_by_id(siswa_id)
    if not siswa:
        return False

    engine = get_engine()
    try:
        with engine.begin() as conn:
            # Delete related absensi records first
            conn.execute(
                text("DELETE FROM absensi WHERE siswa_id = :siswa_id"),
                {"siswa_id": siswa_id},
            )
            # Delete siswa record
            conn.execute(
                text("DELETE FROM siswa WHERE id = :siswa_id"),
                {"siswa_id": siswa_id},
            )

        # Delete QR image file
        qr_path = BARCODE_FOLDER / f"{siswa['kode_qr']}.png"
        if qr_path.exists():
            qr_path.unlink()

        return True
    except SQLAlchemyError as exc:
        raise ValueError("Gagal menghapus data siswa.") from exc
