import hashlib
import hmac
import time
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from backend.app.config import settings

def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with SHA256 and secret key salt."""
    salt = settings.SECRET_KEY.encode('utf-8')
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.b64encode(key).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password."""
    return hash_password(plain_password) == hashed_password

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT Access Token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": int(expire.timestamp())})
    
    # Header & Payload encoding
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode('utf-8')).decode('utf-8').rstrip('=')
    
    signature_raw = f"{header_b64}.{payload_b64}".encode('utf-8')
    signature = hmac.new(settings.SECRET_KEY.encode('utf-8'), signature_raw, hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT Access Token."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        signature_raw = f"{header_b64}.{payload_b64}".encode('utf-8')
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), signature_raw, hashlib.sha256).digest()
        
        # Add padding back
        pad = lambda s: s + '=' * (4 - len(s) % 4) if len(s) % 4 != 0 else s
        actual_sig = base64.urlsafe_b64decode(pad(signature_b64))
        
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        
        payload_bytes = base64.urlsafe_b64decode(pad(payload_b64))
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Check expiration
        if "exp" in payload and payload["exp"] < time.time():
            return None
        
        return payload
    except Exception:
        return None
