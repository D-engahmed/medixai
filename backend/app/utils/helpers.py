"""
Helper utilities and functions
"""
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import json
import re
import uuid
import pytz
from geopy.distance import geodesic
from slugify import slugify

def generate_uuid() -> str:
    """Generate UUID string"""
    return str(uuid.uuid4())

def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case"""
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    return pattern.sub('_', camel_str).lower()

def format_datetime(dt: datetime, timezone: str = 'UTC') -> str:
    """Format datetime to ISO format with timezone"""
    tz = pytz.timezone(timezone)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(tz).isoformat()

def parse_datetime(dt_str: str, timezone: str = 'UTC') -> datetime:
    """Parse datetime string to datetime object"""
    tz = pytz.timezone(timezone)
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    return dt.astimezone(tz)

def calculate_age(birth_date: datetime) -> int:
    """Calculate age from birth date"""
    today = datetime.now()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

def calculate_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: str = 'km'
) -> float:
    """Calculate distance between two coordinates"""
    point1 = (lat1, lon1)
    point2 = (lat2, lon2)
    distance = geodesic(point1, point2)
    return distance.km if unit == 'km' else distance.miles

def generate_slug(text: str) -> str:
    """Generate URL-friendly slug from text"""
    return slugify(text)

def mask_sensitive_data(data: Dict[str, Any], fields: List[str]) -> Dict[str, Any]:
    """Mask sensitive data in dictionary"""
    masked = data.copy()
    for field in fields:
        if field in masked:
            if isinstance(masked[field], str):
                if '@' in masked[field]:  # Email
                    parts = masked[field].split('@')
                    masked[field] = f"{parts[0][:3]}***@{parts[1]}"
                else:  # Other string
                    masked[field] = f"{masked[field][:3]}{'*' * (len(masked[field])-3)}"
            elif isinstance(masked[field], (int, float)):
                masked[field] = '****'
    return masked

def paginate(
    items: List[Any],
    page: int = 1,
    page_size: int = 10
) -> Dict[str, Any]:
    """Paginate list of items"""
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    start = (page - 1) * page_size
    end = start + page_size
    
    return {
        "items": items[start:end],
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

def format_phone_number(phone: str) -> str:
    """Format phone number to international format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if missing
    if not digits.startswith('1'):
        digits = '1' + digits
    
    # Format: +1 (XXX) XXX-XXXX
    return f"+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"

def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format currency amount"""
    symbols = {'USD': '$', 'EUR': '€', 'GBP': '£'}
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"

def time_since(dt: datetime) -> str:
    """Get human-readable time since datetime"""
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "الآن"
    elif diff < timedelta(hours=1):
        minutes = diff.seconds // 60
        return f"منذ {minutes} دقيقة" if minutes == 1 else f"منذ {minutes} دقائق"
    elif diff < timedelta(days=1):
        hours = diff.seconds // 3600
        return f"منذ {hours} ساعة" if hours == 1 else f"منذ {hours} ساعات"
    elif diff < timedelta(days=30):
        days = diff.days
        return f"منذ {days} يوم" if days == 1 else f"منذ {days} أيام"
    elif diff < timedelta(days=365):
        months = diff.days // 30
        return f"منذ {months} شهر" if months == 1 else f"منذ {months} أشهر"
    else:
        years = diff.days // 365
        return f"منذ {years} سنة" if years == 1 else f"منذ {years} سنوات"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result
