from datetime import datetime, timedelta, timezone, date
from typing import Optional

def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format)

def parse_datetime(date_string: str, format: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse string to datetime"""
    return datetime.strptime(date_string, format).replace(tzinfo=timezone.utc)

def time_ago(dt: datetime) -> str:
    """Human-readable time ago"""
    now = utc_now()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"{days} day{'s' if days > 1 else ''} ago"
    else:
        return format_datetime(dt, "%Y-%m-%d")

def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO string format"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()

def from_iso_string(iso_string: str) -> datetime:
    """Parse ISO string to datetime"""
    return datetime.fromisoformat(iso_string)

def start_of_day(dt: datetime) -> datetime:
    """Get start of day (00:00:00) for given datetime"""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)

def end_of_day(dt: datetime) -> datetime:
    """Get end of day (23:59:59.999999) for given datetime"""
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)

def add_business_days(dt: datetime, days: int) -> datetime:
    """Add business days (Monday-Friday) to datetime"""
    current_date = dt.date()
    while days > 0:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5:  # Monday = 0, Friday = 4
            days -= 1
    
    return dt.replace(year=current_date.year, month=current_date.month, day=current_date.day)

def is_business_day(dt: datetime) -> bool:
    """Check if datetime falls on a business day (Monday-Friday)"""
    return dt.weekday() < 5

def get_timezone_offset(dt: datetime) -> str:
    """Get timezone offset string (e.g., '+00:00', '-05:00')"""
    if dt.tzinfo is None:
        return '+00:00'
    
    offset = dt.utcoffset()
    if offset is None:
        return '+00:00'
    
    total_seconds = int(offset.total_seconds())
    hours, remainder = divmod(abs(total_seconds), 3600)
    minutes = remainder // 60
    
    sign = '+' if total_seconds >= 0 else '-'
    return f"{sign}{hours:02d}:{minutes:02d}"

def calculate_duration(start_dt: datetime, end_dt: datetime) -> dict:
    """Calculate duration between two datetimes"""
    diff = end_dt - start_dt
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': seconds,
        'total_seconds': diff.total_seconds(),
        'total_minutes': diff.total_seconds() / 60,
        'total_hours': diff.total_seconds() / 3600,
        'total_days': diff.total_seconds() / 86400
    }

def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date"""
    today = date.today()
    age = today.year - birth_date.year
    
    # Check if birthday hasn't occurred this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return age