# JWT Authentication Implementation Guide

## Problem Description
Endpoints exposed without proper authentication can leak sensitive data and allow unauthorized access to critical functionality.

## Security Best Practices
1. Use the `@xyz_jwt_required()` decorator to protect endpoints.
2. Implement proper token expiration
3. Use secure token transmission (HTTPS)
4. Implement refresh token rotation
5. Add rate limiting for token generation

## Implementation Guide

### 1. Basic Setup
```python
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from datetime import timedelta

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
jwt = JWTManager(app)
```

### 2. Token Generation
```python
@app.route('/auth/token', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if validate_credentials(username, password):
        access_token = create_access_token(
            identity=username,
            additional_claims={'roles': get_user_roles(username)}
        )
        return jsonify({"token": access_token})
    return jsonify({"error": "Invalid credentials"}), 401
```

### 3. Protected Endpoint Implementation
```python
@app.route('/api/protected')
@xyz_jwt_required()
def protected_endpoint():
    current_user = get_jwt_identity()
    claims = get_jwt()
    return jsonify({"user": current_user, "claims": claims})
```
