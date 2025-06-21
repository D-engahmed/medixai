"""
Validation utilities for data validation and sanitization
"""
from typing import Optional, Dict, Any
import re
from datetime import datetime, date
from email_validator import validate_email, EmailNotValidError
from pydantic import ValidationError

def validate_password(password: str) -> Dict[str, Any]:
    """
    Validate password strength
    """
    errors = []
    if len(password) < 8:
        errors.append("كلمة المرور يجب أن تكون 8 أحرف على الأقل")
    if not re.search(r"[A-Z]", password):
        errors.append("كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل")
    if not re.search(r"[a-z]", password):
        errors.append("كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل")
    if not re.search(r"\d", password):
        errors.append("كلمة المرور يجب أن تحتوي على رقم واحد على الأقل")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }

def validate_email_address(email: str) -> Dict[str, Any]:
    """
    Validate email address format
    """
    try:
        validation = validate_email(email, check_deliverability=False)
        email = validation.email
        return {
            "is_valid": True,
            "normalized_email": email,
            "errors": []
        }
    except EmailNotValidError as e:
        return {
            "is_valid": False,
            "normalized_email": None,
            "errors": [str(e)]
        }

def validate_phone_number(phone: str) -> Dict[str, Any]:
    """
    Validate phone number format
    """
    # Remove any whitespace or special characters
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it's a valid international format
    pattern = r'^\+?[1-9]\d{1,14}$'
    is_valid = bool(re.match(pattern, phone))
    
    return {
        "is_valid": is_valid,
        "normalized_phone": phone if is_valid else None,
        "errors": [] if is_valid else ["رقم الهاتف غير صالح"]
    }

def validate_date_of_birth(dob: date) -> Dict[str, Any]:
    """
    Validate date of birth
    """
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    
    errors = []
    if age < 0:
        errors.append("تاريخ الميلاد لا يمكن أن يكون في المستقبل")
    elif age < 18:
        errors.append("يجب أن يكون العمر 18 سنة على الأقل")
    elif age > 120:
        errors.append("تاريخ الميلاد غير صالح")
    
    return {
        "is_valid": len(errors) == 0,
        "age": age if len(errors) == 0 else None,
        "errors": errors
    }

def validate_coordinates(lat: float, lon: float) -> Dict[str, Any]:
    """
    Validate geographical coordinates
    """
    errors = []
    if not -90 <= lat <= 90:
        errors.append("خط العرض يجب أن يكون بين -90 و 90")
    if not -180 <= lon <= 180:
        errors.append("خط الطول يجب أن يكون بين -180 و 180")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }

def sanitize_html(text: str) -> str:
    """
    Remove HTML tags from text
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text)

def validate_file_type(content_type: str, allowed_types: list) -> bool:
    """
    Validate file type
    """
    return content_type.lower() in allowed_types

def validate_file_size(size: int, max_size: int) -> bool:
    """
    Validate file size
    """
    return size <= max_size
