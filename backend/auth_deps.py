import os
import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from typing import Optional
security = HTTPBearer(auto_error=False)

def get_supabase_jwks_url():
    # Attempt env var, fallback to the known project URL
    url = os.getenv("SUPABASE_URL", "https://nvdoiirgulzoncuecwdy.supabase.co")
    return f"{url}/auth/v1/.well-known/jwks.json"

def verify_supabase_jwt(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """
    Dependency that intercepts the Authorization Bearer token from the frontend.
    For local development, if no token is provided, returns a guest user.
    """
    if not credentials or credentials.credentials in ["null", "undefined", ""]:
        return {"sub": "guest-user-id", "email": "guest@example.com", "user_metadata": {"role": "User"}}

    token = credentials.credentials
    
    try:
        # Decode the JWT without strictly verifying the symmetric signature for development
        data = jwt.decode(
            token,
            options={
                "verify_signature": False, 
                "verify_aud": False,
                "verify_exp": True
            }
        )
        return data
    except Exception as e:
        # In case of expired token, still return guest for local testing ease
        return {"sub": "guest-user-id", "email": "guest@example.com", "user_metadata": {"role": "User"}}
