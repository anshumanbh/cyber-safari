from datetime import datetime

def log_progress(message: str, prefix: str = "🔍"):
    """Helper function to log progress with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {prefix} {message}") 