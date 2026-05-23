"""
Attendance (Absensi) management business logic.
"""

from io import BytesIO

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from config import JURUSAN, STATUS_OPTIONS
from db import get_engine
from utils import get_now_time_str, get_today_str


def process_scan_qr(kode_qr: str, status: str = "HADIR") -> dict:
    """
    Process QR code scan for attendance.
    
    Args:
        kode_qr: QR code identifier
        status: Attendance status (default: HADIR)
        
    Returns:
        Dictionary with operation result
    """
    if not kode_qr:
        return {"status": "error", "message": "Kode QR tidak terbaca."}

    status_clean = (status or "HADIR").upper()
    if status_clean not in STATUS_OPTIONS:
        status_clean = "HADIR"

    today = get_today_str()
    now_time = get_now_time_str()
    engine = get_engine()

    try:
        with engine.begin() as conn:
            siswa = conn.execute(
                text(
                    """
                    SELECT id, nama, kelas, jurusan
                    FROM siswa
                    WHERE kode_qr = :kode_qr
                    """
                ),
                {"kode_qr": kode_qr},
            ).mappings().first()

            if not siswa:
                return {"status": "error", "message": "QR Code siswa tidak ditemukan."}

            existing = conn.execute(
                text(
                    """
                    SELECT waktu, status FROM absensi
                    WHERE siswa_id = :siswa_id AND tanggal = :tanggal
                    """
                ),
                {"siswa_id": siswa["id"], "tanggal": today},
            ).mappings().first()
            
            if existing:
                return {
                    "status": "already",
                    "nama": siswa["nama"],
                    "waktu": existing["waktu"],
                    "message": f"{siswa['nama']} sudah tercatat hari ini ({existing['waktu']}).",
                }

            conn.execute(
                text(
                    """
                    INSERT INTO absensi (siswa_id, nama, kelas, jurusan, waktu, tanggal, status)
                    VALUES (:siswa_id, :nama, :kelas, :jurusan, :waktu, :tanggal, :status)
                    """
                ),
                {
                    "siswa_id": siswa["id"],
                    "nama": siswa["nama"],
                    "kelas": siswa["kelas"],
                    "jurusan": siswa["jurusan"],
                    "waktu": now_time,
                    "tanggal": today,
                    "status": status_clean,
                },
            )
    except IntegrityError:
        with engine.connect() as conn:
            existing = conn.execute(
                text(
                    "SELECT waktu FROM absensi WHERE siswa_id = :siswa_id AND tanggal = :tanggal"
                ),
                {"siswa_id": siswa["id"], "tanggal": today},
            ).mappings().first()
        return {
            "status": "already",
            "nama": siswa["nama"],
            "waktu": existing["waktu"] if existing else "-",
            "message": f"{siswa['nama']} sudah tercatat hari ini.",
        }

    return {
        "status": "success",
        "nama": siswa["nama"],
        "kelas": siswa["kelas"],
        "jurusan": siswa["jurusan"],
        "waktu": now_time,
        "message": f"Absensi {siswa['nama']} berhasil.",
    }


def get_dashboard_metrics() -> dict:
    """
    Get dashboard metrics for today's attendance.
    
    Returns:
        Dictionary with attendance metrics
    """
    today = get_today_str()
    engine = get_engine()
    
    with engine.connect() as conn:
        total_siswa = int(
            conn.execute(text("SELECT COUNT(*) AS count FROM siswa")).mappings().first()["count"]
        )
        hadir_hari_ini = int(
            conn.execute(
                text(
                    """
                    SELECT COUNT(*) AS count
                    FROM absensi
                    WHERE tanggal = :tanggal AND status = 'HADIR'
                    """
                ),
                {"tanggal": today},
            ).mappings().first()["count"]
        )

    belum_hadir = max(total_siswa - hadir_hari_ini, 0)
    persentase = round((hadir_hari_ini / total_siswa) * 100, 2) if total_siswa else 0

    return {
        "tanggal": today,
        "total_siswa": total_siswa,
        "hadir_hari_ini": hadir_hari_ini,
        "belum_hadir": belum_hadir,
        "persentase": persentase,
    }


def get_today_jurusan_summary() -> list[dict]:
    """
    Get attendance summary by major for today.
    
    Returns:
        List of attendance summaries per major
    """
    today = get_today_str()
    engine = get_engine()
    
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    s.jurusan,
                    COUNT(s.id) AS total_siswa,
                    SUM(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) AS hadir_count
                FROM siswa s
                LEFT JOIN absensi a
                    ON a.siswa_id = s.id
                   AND a.tanggal = :tanggal
                   AND a.status = 'HADIR'
                GROUP BY s.jurusan
                ORDER BY s.jurusan
                """
            ),
            {"tanggal": today},
        ).mappings().all()

    result: list[dict] = []
    for jurusan in JURUSAN:
        row = next((item for item in rows if item["jurusan"] == jurusan), None)
        result.append(
            {
                "jurusan": jurusan,
                "total_siswa": row["total_siswa"] if row else 0,
                "hadir_count": row["hadir_count"] if row else 0,
            }
        )
    return result


def get_recent_absensi(limit: int = 10) -> list[dict]:
    """
    Get recent attendance records.
    
    Args:
        limit: Number of records to retrieve
        
    Returns:
        List of recent attendance records
    """
    limit_value = max(1, int(limit))
    engine = get_engine()
    
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                f"""
                SELECT id, nama, kelas, jurusan, waktu, tanggal, status
                FROM absensi
                ORDER BY tanggal DESC, waktu DESC, id DESC
                LIMIT {limit_value}
                """
            )
        ).mappings().all()

    return [dict(row) for row in rows]


def get_rekap_absensi(
    start_date: str | None = None,
    end_date: str | None = None,
    jurusan: str | None = None,
    kelas: str | None = None,
    status: str | None = None,
) -> list[dict]:
    """
    Get attendance records with filtering.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        jurusan: Filter by major
        kelas: Filter by class
        status: Filter by status
        
    Returns:
        List of attendance records
    """
    query = """
        SELECT id, nama, kelas, jurusan, waktu, tanggal, status
        FROM absensi
        WHERE 1=1
    """
    params: dict = {}

    if start_date:
        query += " AND tanggal >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND tanggal <= :end_date"
        params["end_date"] = end_date
    if jurusan:
        query += " AND jurusan = :jurusan"
        params["jurusan"] = jurusan.upper()
    if kelas:
        query += " AND kelas = :kelas"
        params["kelas"] = kelas.upper()
    if status:
        query += " AND status = :status"
        params["status"] = status.upper()

    query += " ORDER BY tanggal DESC, waktu DESC, id DESC"

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    return [dict(row) for row in rows]


def get_rekap_stats_per_kelas(
    start_date: str | None = None,
    end_date: str | None = None,
    jurusan: str | None = None,
    kelas: str | None = None,
) -> list[dict]:
    """
    Get attendance statistics per class.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        jurusan: Filter by major
        kelas: Filter by class
        
    Returns:
        List of statistics per class
    """
    query = """
        SELECT
            kelas,
            COUNT(*) AS total_absensi,
            SUM(CASE WHEN status = 'HADIR' THEN 1 ELSE 0 END) AS hadir,
            SUM(CASE WHEN status = 'IZIN' THEN 1 ELSE 0 END) AS izin,
            SUM(CASE WHEN status = 'SAKIT' THEN 1 ELSE 0 END) AS sakit,
            SUM(CASE WHEN status = 'ALPHA' THEN 1 ELSE 0 END) AS alpha
        FROM absensi
        WHERE 1=1
    """
    params: dict = {}

    if start_date:
        query += " AND tanggal >= :start_date"
        params["start_date"] = start_date
    if end_date:
        query += " AND tanggal <= :end_date"
        params["end_date"] = end_date
    if jurusan:
        query += " AND jurusan = :jurusan"
        params["jurusan"] = jurusan.upper()
    if kelas:
        query += " AND kelas = :kelas"
        params["kelas"] = kelas.upper()

    query += " GROUP BY kelas ORDER BY kelas"

    engine = get_engine()
    with engine.connect() as conn:
        rows = conn.execute(text(query), params).mappings().all()

    return [dict(row) for row in rows]


def export_rekap_excel(
    start_date: str | None = None,
    end_date: str | None = None,
    jurusan: str | None = None,
    kelas: str | None = None,
    status: str | None = None,
) -> BytesIO:
    """
    Export attendance records to Excel.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        jurusan: Filter by major
        kelas: Filter by class
        status: Filter by status
        
    Returns:
        BytesIO object with Excel file
    """
    rows = get_rekap_absensi(start_date, end_date, jurusan, kelas, status)
    columns = ["id", "nama", "kelas", "jurusan", "waktu", "tanggal", "status"]
    df = pd.DataFrame(rows, columns=columns)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Rekap Absensi")

    output.seek(0)
    return output


def set_manual_status(siswa_id: int, status: str, tanggal: str | None = None) -> dict:
    """
    Set or update attendance status manually (by admin).
    
    If a record exists for the student on that date, update it.
    If not, insert a new record.
    
    Args:
        siswa_id: Student ID
        status: Attendance status (HADIR, IZIN, SAKIT, ALPHA)
        tanggal: Date string (defaults to today)
        
    Returns:
        Dict with operation result
    """
    from utils import get_today_str, get_now_time_str

    tanggal = tanggal or get_today_str()
    status_clean = (status or "").strip().upper()

    if status_clean not in STATUS_OPTIONS:
        return {"status": "error", "message": f"Status '{status}' tidak valid."}

    engine = get_engine()

    with engine.connect() as conn:
        siswa = conn.execute(
            text("SELECT id, nama, kelas, jurusan FROM siswa WHERE id = :siswa_id"),
            {"siswa_id": siswa_id},
        ).mappings().first()

    if not siswa:
        return {"status": "error", "message": "Siswa tidak ditemukan."}

    now_time = get_now_time_str()

    try:
        with engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT id FROM absensi WHERE siswa_id = :siswa_id AND tanggal = :tanggal"
                ),
                {"siswa_id": siswa_id, "tanggal": tanggal},
            ).mappings().first()

            if existing:
                conn.execute(
                    text(
                        """
                        UPDATE absensi 
                        SET status = :status, waktu = :waktu 
                        WHERE siswa_id = :siswa_id AND tanggal = :tanggal
                        """
                    ),
                    {
                        "status": status_clean,
                        "waktu": now_time,
                        "siswa_id": siswa_id,
                        "tanggal": tanggal,
                    },
                )
            else:
                conn.execute(
                    text(
                        """
                        INSERT INTO absensi (siswa_id, nama, kelas, jurusan, waktu, tanggal, status)
                        VALUES (:siswa_id, :nama, :kelas, :jurusan, :waktu, :tanggal, :status)
                        """
                    ),
                    {
                        "siswa_id": siswa_id,
                        "nama": siswa["nama"],
                        "kelas": siswa["kelas"],
                        "jurusan": siswa["jurusan"],
                        "waktu": now_time,
                        "tanggal": tanggal,
                        "status": status_clean,
                    },
                )
    except IntegrityError:
        return {"status": "error", "message": "Gagal menyimpan status absensi."}

    return {
        "status": "success",
        "message": f"Status {siswa['nama']} diubah menjadi {status_clean}.",
        "data": {
            "siswa_id": siswa_id,
            "nama": siswa["nama"],
            "status": status_clean,
            "tanggal": tanggal,
        },
    }


def get_today_attendance_map(tanggal: str | None = None) -> dict:
    """
    Get a mapping of siswa_id -> attendance info for a given date.
    
    Args:
        tanggal: Date string (defaults to today)
        
    Returns:
        Dict mapping siswa_id to {"status": str, "waktu": str}
    """
    from utils import get_today_str

    tanggal = tanggal or get_today_str()
    engine = get_engine()

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT siswa_id, status, waktu
                FROM absensi
                WHERE tanggal = :tanggal
                """
            ),
            {"tanggal": tanggal},
        ).mappings().all()

    return {
        row["siswa_id"]: {"status": row["status"], "waktu": row["waktu"]}
        for row in rows
    }

