"""
Database initialization and connection management.
"""

import os
import shutil
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from config import (
    BARCODE_FOLDER,
    DATABASE_URL,
    DB_AUTO_FALLBACK_SQLITE,
    DB_BACKUP_NAME,
    DB_NAME,
    SQLITE_DATABASE_URL,
    TIDB_SSL_CA,
)


_ENGINE: Engine | None = None
_ACTIVE_PROVIDER: str = "sqlite"


def _create_engine(url: str) -> Engine:
    """
    Create a SQLAlchemy engine with appropriate configuration.
    
    Args:
        url: Database URL
        
    Returns:
        Configured SQLAlchemy Engine
    """
    connect_args = {}
    if url.startswith("mysql+"):
        ssl_config: dict = {"ca": TIDB_SSL_CA or ""}
        connect_args["ssl"] = ssl_config

    return create_engine(
        url,
        future=True,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def _is_tidb_url(url: str) -> bool:
    """Check if URL is TiDB (MySQL)."""
    return url.startswith("mysql+")


def _verify_engine(engine: Engine) -> None:
    """Verify database connection is working."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


def _build_engine() -> tuple[Engine, str]:
    """
    Build the primary database engine with fallback to SQLite if needed.
    
    Returns:
        Tuple of (Engine, provider_name)
    """
    primary_engine = _create_engine(DATABASE_URL)
    primary_provider = "tidb" if _is_tidb_url(DATABASE_URL) else "sqlite"

    try:
        _verify_engine(primary_engine)
        return primary_engine, primary_provider
    except SQLAlchemyError:
        if primary_provider == "tidb" and DB_AUTO_FALLBACK_SQLITE:
            fallback_engine = _create_engine(SQLITE_DATABASE_URL)
            _verify_engine(fallback_engine)
            return fallback_engine, "sqlite"
        raise


def _initialize_engine() -> None:
    """Initialize the global database engine."""
    global _ENGINE, _ACTIVE_PROVIDER
    _ENGINE, _ACTIVE_PROVIDER = _build_engine()


def using_tidb() -> bool:
    """Check if currently using TiDB."""
    return _ACTIVE_PROVIDER == "tidb"


def get_connection() -> Connection:
    """Get a new database connection."""
    if _ENGINE is None:
        _initialize_engine()
    return _ENGINE.connect()


def get_engine() -> Engine:
    """Get the global database engine."""
    if _ENGINE is None:
        _initialize_engine()
    return _ENGINE


def _fetch_table_names(conn: Connection) -> set[str]:
    """Fetch all table names from the database."""
    if using_tidb():
        rows = conn.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                """
            )
        ).mappings().all()
        return {row["table_name"] for row in rows}

    rows = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table'")
    ).mappings().all()
    return {row["name"] for row in rows}


def _get_table_columns(conn: Connection, table_name: str) -> set[str]:
    """Fetch all column names from a specific table."""
    if using_tidb():
        rows = conn.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE() AND table_name = :table_name
                """
            ),
            {"table_name": table_name},
        ).mappings().all()
        return {row["column_name"] for row in rows}

    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).mappings().all()
    return {row["name"] for row in rows}


def _schema_needs_reset(conn: Connection) -> bool:
    """Check if the database schema needs to be reset/recreated."""
    tables = _fetch_table_names(conn)

    if "karyawan" in tables:
        return True

    required_tables = {"siswa", "absensi"}
    if not required_tables.issubset(tables):
        return True

    siswa_cols = _get_table_columns(conn, "siswa")
    absensi_cols = _get_table_columns(conn, "absensi")

    expected_siswa_cols = {"id", "nis", "nama", "jurusan", "kelas", "kode_qr"}
    expected_absensi_cols = {
        "id",
        "siswa_id",
        "nama",
        "kelas",
        "jurusan",
        "waktu",
        "tanggal",
        "status",
    }

    return not (
        expected_siswa_cols.issubset(siswa_cols)
        and expected_absensi_cols.issubset(absensi_cols)
    )


def _backup_database() -> None:
    """Backup the current database."""
    if not os.path.exists(DB_NAME):
        return

    backup_path = Path(DB_BACKUP_NAME)
    if backup_path.exists():
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        old_backup = backup_path.with_name(f"absensi_backup_{timestamp}.db")
        shutil.copy2(backup_path, old_backup)

    shutil.copy2(DB_NAME, DB_BACKUP_NAME)


def _drop_current_schema(conn: Connection) -> None:
    """Drop all schema tables."""
    conn.execute(text("DROP TABLE IF EXISTS absensi"))
    conn.execute(text("DROP TABLE IF EXISTS siswa"))
    conn.execute(text("DROP TABLE IF EXISTS karyawan"))


def _create_schema(conn: Connection) -> None:
    """Create the database schema."""
    if using_tidb():
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS siswa (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    nis VARCHAR(64) NOT NULL UNIQUE,
                    nama VARCHAR(255) NOT NULL,
                    jurusan VARCHAR(20) NOT NULL,
                    kelas VARCHAR(50) NOT NULL,
                    kode_qr VARCHAR(255) NOT NULL UNIQUE
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS absensi (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    siswa_id BIGINT NOT NULL,
                    nama VARCHAR(255) NOT NULL,
                    kelas VARCHAR(50) NOT NULL,
                    jurusan VARCHAR(20) NOT NULL,
                    waktu VARCHAR(16) NOT NULL,
                    tanggal VARCHAR(16) NOT NULL,
                    status VARCHAR(10) NOT NULL,
                    UNIQUE KEY uniq_absensi_harian (siswa_id, tanggal),
                    INDEX idx_absensi_tanggal (tanggal),
                    INDEX idx_absensi_kelas (kelas),
                    INDEX idx_absensi_jurusan (jurusan),
                    CONSTRAINT fk_absensi_siswa FOREIGN KEY (siswa_id) REFERENCES siswa(id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS saturday_token (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    token VARCHAR(20) NOT NULL,
                    tanggal VARCHAR(16) NOT NULL UNIQUE,
                    created_at VARCHAR(30) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS token_redemption (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    siswa_id BIGINT NOT NULL,
                    tanggal VARCHAR(16) NOT NULL,
                    redeemed_at VARCHAR(30) NOT NULL,
                    UNIQUE KEY uniq_redemption (siswa_id, tanggal),
                    CONSTRAINT fk_redemption_siswa FOREIGN KEY (siswa_id) REFERENCES siswa(id)
                )
                """
            )
        )
        return

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS siswa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nis TEXT UNIQUE NOT NULL,
                nama TEXT NOT NULL,
                jurusan TEXT NOT NULL,
                kelas TEXT NOT NULL,
                kode_qr TEXT UNIQUE NOT NULL
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS absensi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siswa_id INTEGER NOT NULL,
                nama TEXT NOT NULL,
                kelas TEXT NOT NULL,
                jurusan TEXT NOT NULL,
                waktu TEXT NOT NULL,
                tanggal TEXT NOT NULL,
                status TEXT NOT NULL,
                FOREIGN KEY(siswa_id) REFERENCES siswa(id)
            )
            """
        )
    )
    conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_absensi_harian ON absensi(siswa_id, tanggal)"
        )
    )
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_absensi_tanggal ON absensi(tanggal)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_absensi_kelas ON absensi(kelas)"))
    conn.execute(text("CREATE INDEX IF NOT EXISTS idx_absensi_jurusan ON absensi(jurusan)"))
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS saturday_token (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                tanggal TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            )
            """
        )
    )
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS token_redemption (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siswa_id INTEGER NOT NULL,
                tanggal TEXT NOT NULL,
                redeemed_at TEXT NOT NULL,
                FOREIGN KEY(siswa_id) REFERENCES siswa(id)
            )
            """
        )
    )
    conn.execute(
        text(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_redemption_unique ON token_redemption(siswa_id, tanggal)"
        )
    )


def initialize_database() -> None:
    """Initialize the database, creating schema if needed."""
    global _ENGINE, _ACTIVE_PROVIDER

    _initialize_engine()

    BARCODE_FOLDER.mkdir(parents=True, exist_ok=True)

    if not using_tidb() and os.path.exists(DB_NAME):
        with _ENGINE.connect() as conn:
            needs_reset = _schema_needs_reset(conn)

        if needs_reset:
            _backup_database()
            _ENGINE.dispose()
            os.remove(DB_NAME)
            _ENGINE = _create_engine(SQLITE_DATABASE_URL)
            _ACTIVE_PROVIDER = "sqlite"

    with _ENGINE.begin() as conn:
        needs_reset = _schema_needs_reset(conn)
        if needs_reset and using_tidb():
            _drop_current_schema(conn)

        _create_schema(conn)


def init_db() -> None:
    """Alias for initialize_database()."""
    initialize_database()
