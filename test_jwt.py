"""Test JWT token generation and decoding"""
from app.auth import create_access_token, decode_access_token
from app.config import get_settings

# Test token creation and decoding (sub must be string)
token = create_access_token(data={"sub": "1", "username": "admin"})
print(f"Generated token: {token[:50]}...")

decoded = decode_access_token(token)
print(f"Decoded token: {decoded}")

if decoded:
    print(f"✅ Token is valid!")
    print(f"   User ID: {decoded.user_id}")
    print(f"   Username: {decoded.username}")
else:
    print(f"❌ Token is invalid!")

# Check SECRET_KEY
settings = get_settings()
print(f"\nSECRET_KEY length: {len(settings.secret_key)}")
print(f"SECRET_KEY: {settings.secret_key[:20]}...")
