import os
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency fallback
    load_dotenv = None

# Timezone: WIB (Waktu Indonesia Barat / Asia/Jakarta)
TZ_WIB = ZoneInfo("Asia/Jakarta")

BASE_DIR = Path(__file__).resolve().parent

if load_dotenv is not None:
    load_dotenv(BASE_DIR / ".env", override=True)

# Vercel filesystem is ephemeral and read-only except /tmp
if os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"):
    SQLITE_DB_NAME = "/tmp/absensi.db"
    SQLITE_DB_BACKUP_NAME = "/tmp/absensi_backup.db"
    BARCODE_FOLDER = Path("/tmp/barcodes")
else:
    SQLITE_DB_NAME = str(BASE_DIR / "absensi.db")
    SQLITE_DB_BACKUP_NAME = str(BASE_DIR / "absensi_backup.db")
    BARCODE_FOLDER = BASE_DIR / "static" / "barcodes"

DB_NAME = SQLITE_DB_NAME
DB_BACKUP_NAME = SQLITE_DB_BACKUP_NAME

DB_PROVIDER = os.environ.get("DB_PROVIDER", "tidb").strip().lower()
DB_AUTO_FALLBACK_SQLITE = (
    os.environ.get("DB_AUTO_FALLBACK_SQLITE", "1").strip().lower()
    in {"1", "true", "yes", "y"}
)

TIDB_HOST = os.environ.get("TIDB_HOST", "127.0.0.1")
TIDB_PORT = int(os.environ.get("TIDB_PORT", "4000"))
TIDB_USER = os.environ.get("TIDB_USER", "root")
TIDB_PASSWORD = os.environ.get("TIDB_PASSWORD", "")
TIDB_DATABASE = os.environ.get("TIDB_DATABASE", "absensi_smk")
TIDB_SSL_CA = os.environ.get("TIDB_SSL_CA", "")


def _tidb_url() -> str:
    encoded_user = quote_plus(TIDB_USER)
    encoded_pass = quote_plus(TIDB_PASSWORD)
    auth = f"{encoded_user}:{encoded_pass}" if TIDB_PASSWORD else encoded_user

    base_url = f"mysql+pymysql://{auth}@{TIDB_HOST}:{TIDB_PORT}/{TIDB_DATABASE}"
    return f"{base_url}?charset=utf8mb4"


def _normalize_database_url(url: str) -> str:
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)
    return url


def get_now_wib() -> datetime:
    """Get current datetime in WIB timezone."""
    return datetime.now(tz=TZ_WIB)


def get_today_str() -> str:
    """Get today's date as string in YYYY-MM-DD format (WIB)."""
    return get_now_wib().strftime("%Y-%m-%d")


def get_now_time_str() -> str:
    """Get current time as string in HH:MM:SS format (WIB)."""
    return get_now_wib().strftime("%H:%M:%S")


def format_waktu_display(waktu_str: str) -> str:
    """Format time string to display format HH:MM (e.g., 14:35)."""
    try:
        return waktu_str[:5]  # HH:MM
    except (AttributeError, TypeError, IndexError):
        return waktu_str


def format_tanggal_display(tanggal_str: str) -> str:
    """Format date string to Indonesian display format (e.g., 28 Apr 2026)."""
    try:
        date_obj = datetime.strptime(tanggal_str, "%Y-%m-%d").date()
        months_id = [
            "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
            "Jul", "Agu", "Sep", "Okt", "Nov", "Des",
        ]
        month_name = months_id[date_obj.month - 1]
        return f"{date_obj.day} {month_name} {date_obj.year}"
    except (ValueError, AttributeError, TypeError, IndexError):
        return tanggal_str


def build_database_url(provider: str | None = None) -> str:
    provider_name = (provider or DB_PROVIDER).strip().lower()
    if provider_name == "tidb":
        return _tidb_url()
    return f"sqlite:///{SQLITE_DB_NAME}"


SQLITE_DATABASE_URL = f"sqlite:///{SQLITE_DB_NAME}"
DATABASE_URL = _normalize_database_url(
    os.environ.get("DATABASE_URL", build_database_url(DB_PROVIDER))
)

SECRET_KEY = os.environ.get("SECRET_KEY", "smk-absensi-qrcode-secret")
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "bulutangkis-tb")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "hehe890")
REMEMBER_COOKIE_DAYS = int(os.environ.get("REMEMBER_COOKIE_DAYS", "30"))
HOST = "0.0.0.0"
PORT = 8080
SSL_CONTEXT = "adhoc"

JURUSAN = ["RPL", "TAV", "TKR", "TITL"]
TINGKAT = ["X", "XI", "XII"]

# Distribusi paralel per jurusan untuk setiap tingkat bisa diubah sesuai kebutuhan sekolah.
PARALLEL_PER_JURUSAN = {
    "RPL": 6,   # 6 paralel × 3 tingkat = 18 kelas
    "TAV": 3,
    "TKR": 3,
    "TITL": 3,
}

# Optional override: {"X": {"RPL": 6, "TKR": 3}, "XI": {...}, "XII": {...}}
PARALLEL_OVERRIDE = {}

STATUS_OPTIONS = ["HADIR", "IZIN", "SAKIT", "ALPHA"]


def generate_kelas_list(parallel_map):
    kelas = []
    for tingkat in TINGKAT:
        for jurusan in JURUSAN:
            tingkat_override = PARALLEL_OVERRIDE.get(tingkat, {})
            jumlah_paralel = int(tingkat_override.get(jurusan, parallel_map.get(jurusan, 0)))
            for nomor in range(1, jumlah_paralel + 1):
                kelas.append(f"{tingkat} {jurusan} {nomor}")
    return kelas


KELAS_LIST = generate_kelas_list(PARALLEL_PER_JURUSAN)

KELAS_BY_JURUSAN = {
    jurusan: [item for item in KELAS_LIST if f" {jurusan} " in item]
    for jurusan in JURUSAN
}


def kelas_by_jurusan(jurusan):
    jurusan = (jurusan or "").upper()
    if not jurusan:
        return KELAS_LIST
    return KELAS_BY_JURUSAN.get(jurusan, [])


# Backward-compatible aliases for modules that still use old names.
DB_PATH = DB_NAME
BACKUP_DB_PATH = DB_BACKUP_NAME
VALID_STATUS = STATUS_OPTIONS
