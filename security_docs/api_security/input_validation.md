# Input Validation Security Guide

## Problem Description
Insufficient input validation can lead to injection attacks, XSS, and other security vulnerabilities.

## Security Implications
- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Buffer Overflows
- Data Corruption

## Implementation Guide

### 1. Request Validation
```python
from marshmallow import Schema, fields, validate

class UserInputSchema(Schema):
    username = fields.Str(required=True, validate=[
        validate.Length(min=3, max=50),
        validate.Regexp('^[a-zA-Z0-9_]+$')
    ])
    email = fields.Email(required=True)
    age = fields.Int(validate=validate.Range(min=0, max=150))

def validate_input(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        schema = UserInputSchema()
        errors = schema.validate(request.get_json())
        if errors:
            return jsonify({"errors": errors}), 400
        return f(*args, **kwargs)
    return decorated
```

### 2. SQL Injection Prevention
```python
from sqlalchemy import text

def safe_query(user_id: int):
    # Use parameterized queries
    query = text('SELECT * FROM users WHERE id = :user_id')
    result = db.session.execute(query, {'user_id': user_id})
```

### 3. XSS Prevention
```python
import bleach

def sanitize_html(content: str) -> str:
    allowed_tags = ['p', 'br', 'strong', 'em']
    allowed_attrs = {'*': ['class']}
    return bleach.clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
```

## Security Best Practices
1. Validate all input data
2. Use parameterized queries
3. Implement proper encoding
4. Sanitize HTML/markdown input
5. Implement content security policy