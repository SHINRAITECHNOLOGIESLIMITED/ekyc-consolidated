"""
Serial Number Normalizer Module

Provides normalization functions for serial numbers to enable consistent comparison
between document-extracted values and IPRS API responses.

Requirements: 1.2, 2.3, 8.3
"""

from typing import Optional


def normalize_serial_number(serial: Optional[str]) -> Optional[str]:
    """
    Normalize a serial number for comparison.
    
    Normalization rules:
    - Convert to uppercase
    - Remove spaces, hyphens, dots
    - Strip leading/trailing whitespace
    - Return None if input is None or empty after normalization
    
    Args:
        serial: Raw serial number string
        
    Returns:
        Normalized serial number or None if invalid
        
    Examples:
        >>> normalize_serial_number("12345-ABC")
        '12345ABC'
        >>> normalize_serial_number("12345 ABC")
        '12345ABC'
        >>> normalize_serial_number("12345.ABC")
        '12345ABC'
        >>> normalize_serial_number("12345-abc")
        '12345ABC'
        >>> normalize_serial_number("  12345-ABC  ")
        '12345ABC'
        >>> normalize_serial_number("")
        None
        >>> normalize_serial_number("---")
        None
        >>> normalize_serial_number(None)
        None
    """
    if serial is None:
        return None
    
    # Strip whitespace first
    result = serial.strip()
    
    if not result:
        return None
    
    # Convert to uppercase
    result = result.upper()
    
    # Remove spaces, hyphens, and dots
    result = result.replace(' ', '')
    result = result.replace('-', '')
    result = result.replace('.', '')
    
    # Return None if empty after normalization
    if not result:
        return None
    
    return result


def normalize_gender(gender: Optional[str]) -> Optional[str]:
    """
    Normalize a gender value for comparison.
    
    Normalization rules:
    - Convert to uppercase single character (M or F)
    - Handle variations: Male/Female, M/F, m/f
    - Return None if input is None, empty, or unrecognized
    
    Args:
        gender: Raw gender string
        
    Returns:
        Normalized gender ('M' or 'F') or None if invalid
        
    Examples:
        >>> normalize_gender("M")
        'M'
        >>> normalize_gender("m")
        'M'
        >>> normalize_gender("Male")
        'M'
        >>> normalize_gender("MALE")
        'M'
        >>> normalize_gender("F")
        'F'
        >>> normalize_gender("Female")
        'F'
        >>> normalize_gender("")
        None
        >>> normalize_gender(None)
        None
        >>> normalize_gender("Unknown")
        None
    """
    if gender is None:
        return None
    
    # Strip whitespace and convert to uppercase
    result = gender.strip().upper()
    
    if not result:
        return None
    
    # Map variations to single character
    if result in ('M', 'MALE'):
        return 'M'
    elif result in ('F', 'FEMALE'):
        return 'F'
    else:
        return None
