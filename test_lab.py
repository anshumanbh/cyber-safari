from flask import Flask, request, jsonify
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
import os

app = Flask(__name__)

class AppLogger:
    """Simple application logger that handles both access and security events"""
    def __init__(self):
        self.log_directory = "app_logs"
        if not os.path.exists(self.log_directory):
            os.makedirs(self.log_directory)
        
        # Create logger
        self.logger = logging.getLogger('app_logger')
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate logs
        self.logger.propagate = False
        
        # Setup handler if it doesn't exist
        if not self.logger.handlers:
            # Create rotating file handler
            handler = RotatingFileHandler(
                f"{self.log_directory}/app.log",
                maxBytes=10000000,  # 10MB
                backupCount=5
            )
            
            # Create formatter
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_event(self, event_type: str, details: str, level: str = "INFO"):
        """Log an application event with structured data"""
        event_data = {
            "event_type": event_type,
            "details": details,
            "ip": request.remote_addr if request else "N/A",
            "path": request.path if request else "N/A",
            "method": request.method if request else "N/A",
            "headers": dict(request.headers) if request else {}
        }
        
        message = json.dumps(event_data)
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        else:
            self.logger.info(message)

# Initialize logger
logger = AppLogger()

# Vulnerable JavaScript file that will be served
VULNERABLE_JS = """
// API Configuration
const API_CONFIG = {
    userInfo: '/api/v1/user-info',  // Leaks sensitive data without auth
    adminPanel: '/api/v1/admin',    // Requires specific admin key
    userProfile: '/api/v1/profile', // Requires X-User-Id header
};

// Admin key hardcoded (security vulnerability)
const ADMIN_KEY = 'super_secret_admin_key_123';

// Function to fetch user info (no auth required - vulnerability)
async function fetchUserInfo() {
    const response = await fetch('/api/v1/user-info');
    return response.json();
}

// Function to access admin panel
async function accessAdminPanel() {
    const headers = {
        'Content-Type': 'application/json',
        'X-Admin-Key': ADMIN_KEY  // Hardcoded admin key usage
    };
    
    const response = await fetch('/api/v1/admin', {
        headers: headers
    });
    return response.json();
}

// Function to get user profile
async function getUserProfile(userId) {
    const headers = {
        'X-User-Id': userId  // Required custom header
    };
    
    const response = await fetch('/api/v1/profile', {
        headers: headers
    });
    return response.json();
}

"""

@app.route('/main.js')
def serve_js():
    logger.log_event(event_type="ServeJS", details="Served main.js")
    return VULNERABLE_JS, 200, {'Content-Type': 'application/javascript'}

@app.route('/api/v1/user-info')
def user_info():
    logger.log_event(event_type="UserInfoAccess", details="Accessed user info endpoint")
    # Vulnerable: Returns sensitive information without authentication
    return jsonify({
        "users": [
            {"id": "1", "name": "John Doe", "ssn": "123-45-6789", "salary": 75000},
            {"id": "2", "name": "Jane Smith", "ssn": "987-65-4321", "salary": 82000}
        ],
        "database_connection": "mongodb://admin:password@localhost:27017",
        "api_keys": {
            "stripe": "sk_test_123456789",
            "aws": "AKIA1234567890EXAMPLE"
        }
    })

@app.route('/api/v1/profile')
def user_profile():
    user_id = request.headers.get('X-User-Id')
    if not user_id:
        logger.log_event(event_type="UserProfileAccessDenied", details="Missing X-User-Id header", level="WARNING")
        return jsonify({"error": "X-User-Id header is required"}), 401
    
    logger.log_event(event_type="UserProfileAccess", details=f"Accessed profile for user_id: {user_id}")
    return jsonify({
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "role": "user"
    })

@app.route('/api/v1/admin')
def admin_panel():
    admin_key = request.headers.get('X-Admin-Key')
    if not admin_key:
        logger.log_event(event_type="AdminPanelAccessDenied", details="Missing X-Admin-Key header", level="WARNING")
        return jsonify({"error": "X-Admin-Key header is required"}), 401
    
    if admin_key != 'super_secret_admin_key_123':  # Hardcoded key check
        logger.log_event(event_type="AdminPanelAccessDenied", details="Invalid admin key", level="ERROR")
        return jsonify({"error": "Invalid admin key"}), 403
    
    logger.log_event(event_type="AdminPanelAccess", details="Accessed admin panel")
    return jsonify({
        "sensitive_data": "This is sensitive admin data",
        "internal_keys": {
            "database": "root:password123",
            "api_gateway": "private_key_xyz"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)