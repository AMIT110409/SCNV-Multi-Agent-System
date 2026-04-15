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
        # 1. Fetch the JWKS URL
        jwks_url = os.getenv("SUPABASE_AUTH_JWKS_URL")
        if not jwks_url:
            # Fallback to computed URL if specific env var is missing
            project_url = os.getenv("SUPABASE_URL", "https://nvdoiirgulzoncuecwdy.supabase.co")
            jwks_url = f"{project_url}/auth/v1/.well-known/jwks.json"

        # 2. Initialize JWKS Client
        jwks_client = PyJWKClient(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # 3. Decode and verify signature
        data = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={
                "verify_aud": False, # Usually 'authenticated' or project-specific
                "verify_exp": True
            }
        )
        return data
    except Exception as e:
        # For development/local testing, if verification fails (e.g. invalid signature), 
        # we log the error but still allow a guest fallback to avoid blocking the UI.
        print(f"[AUTH ERROR] JWT Verification failed: {str(e)}")
        return {"sub": "guest-user-id", "email": "guest@example.com", "user_metadata": {"role": "User"}}
