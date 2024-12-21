# Role-Based Access Control (RBAC) Implementation Guide

## Problem Description
Applications need granular control over user permissions and access rights to protect sensitive operations and data.

## Security Implications
- Unauthorized access to features
- Privilege escalation
- Insufficient access controls
- Audit compliance issues

## Implementation Guide

### 1. RBAC Structure
```python
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    permissions = db.Column(db.JSON)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roles = db.relationship('Role', secondary='user_roles')
```

### 2. Permission Checking
```python
def permission_required(permission):
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_roles = get_user_roles(claims['sub'])
            
            if not has_permission(user_roles, permission):
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
```

## Security Best Practices
1. Implement principle of least privilege
2. Regular role audits
3. Implement role hierarchies
4. Log permission changes
5. Separate duty concerns