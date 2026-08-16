"""
Utility functions for formatting and datetime operations.
"""

from datetime import datetime
from zoneinfo import ZoneInfo


TZ_WIB = ZoneInfo("Asia/Jakarta")


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
    """
    Format time string to display format HH:MM (e.g., 14:35).
    
    Args:
        waktu_str: Time string in HH:MM:SS format
        
    Returns:
        Formatted time string HH:MM or original if error
    """
    try:
        return waktu_str[:5]  # HH:MM
    except (AttributeError, TypeError, IndexError):
        return waktu_str


def format_tanggal_display(tanggal_str: str) -> str:
    """
    Format date string to Indonesian display format (e.g., 28 Apr 2026).
    
    Args:
        tanggal_str: Date string in YYYY-MM-DD format
        
    Returns:
        Formatted date in Indonesian format or original if error
    """
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
