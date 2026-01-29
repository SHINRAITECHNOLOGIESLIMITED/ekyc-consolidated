---
inclusion: fileMatch
fileMatchPattern: "**/iprs.py"
---

# IPRS Integration Guidelines

This steering file is automatically included when working with IPRS-related files.

## IPRS API Overview

The IPRS (Integrated Population Registration System) is Kenya's national identity database. Our integration uses the Jubilee ESB layer.

## API Endpoints

### National ID Verification
```python
from iprs import verify_national_id

response = verify_national_id(id_number="12345678")
# Returns: citizen details including name, DOB, gender, photo
```

### Response Fields
Key fields returned by IPRS:
- `first_name`, `surname`, `other_name` - Name components
- `date_of_birth` - Format: YYYY-MM-DD
- `gender` - "M" or "F"
- `serial_number` - Latest document serial number
- `photo` - Base64 encoded photo

## Gender Validation

IPRS returns gender as single character:
- `"M"` = Male
- `"F"` = Female

When validating against document-extracted gender:
```python
GENDER_MAPPINGS = {
    "male": "M", "m": "M", "M": "M",
    "female": "F", "f": "F", "F": "F"
}
```

## Serial Number Validation

IPRS returns the latest serial number for a national ID. Compare against document serial:
```python
def validate_serial(document_serial: str, iprs_serial: str) -> bool:
    return document_serial.strip().upper() == iprs_serial.strip().upper()
```

## Error Handling

Common IPRS error scenarios:
- `ID_NOT_FOUND` - National ID doesn't exist in IPRS
- `SERVICE_UNAVAILABLE` - IPRS API is down
- `INVALID_FORMAT` - ID number format is invalid
- `TIMEOUT` - Request exceeded timeout threshold

## Important Notes

1. **Data Quality**: IPRS is the authoritative source for Kenyan citizen data
2. **Rate Limiting**: Be mindful of API rate limits
3. **Caching**: Consider caching IPRS responses for the same session
4. **Privacy**: IPRS data is sensitive - log only necessary fields
