"""Debug token creation and validation."""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from jose import jwt, JWTError
from app.core.config import get_settings
from app.core.security import create_access_token, decode_token

settings = get_settings()

# Create a test token
print("1. Creating test token...")
token_data = {"sub": "1", "role": "admin"}
token = create_access_token(token_data)
print(f"   Token: {token[:50]}...")
print(f"   Full token length: {len(token)}")

# Try to decode with jose directly
print("\n2. Decoding with jose directly...")
try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    print(f"   ✓ Success!")
    print(f"   Payload: {payload}")
except JWTError as e:
    print(f"   ✗ Failed: {e}")

# Try to decode with our decode_token function
print("\n3. Decoding with our decode_token function...")
try:
    payload = decode_token(token)
    print(f"   ✓ Success!")
    print(f"   Payload: {payload}")
except Exception as e:
    print(f"   ✗ Failed: {e}")
