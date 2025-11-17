"""
Authentication service with Firebase Auth integration
"""

import os
import secrets
from typing import Optional, Dict
from fastapi import HTTPException, Security, status, Header
from fastapi.security import APIKeyHeader
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth


class AuthService:
    """Firebase Authentication + API key fallback"""
    
    def __init__(self):
        # Initialize Firebase Admin
        self.firebase_initialized = False
        self._init_firebase()
        
        # API key fallback for development
        self.api_keys = set(os.getenv('API_KEYS', '').split(','))
        
        if not self.api_keys or self.api_keys == {''}:
            default_key = secrets.token_urlsafe(32)
            self.api_keys = {default_key}
            print(f"⚠️  Generated API Key: {default_key}")
        
        self.api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
    
    def _init_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if already initialized
            firebase_admin.get_app()
            self.firebase_initialized = True
            print("✅ Firebase Admin already initialized")
        except ValueError:
            # Not initialized, try to initialize
            try:
                # Try to use service account file
                cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
                if cred_path and os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                    self.firebase_initialized = True
                    print("✅ Firebase Admin initialized with service account")
                else:
                    # Use default credentials (works in Cloud Run)
                    firebase_admin.initialize_app()
                    self.firebase_initialized = True
                    print("✅ Firebase Admin initialized with default credentials")
            except Exception as e:
                print(f"⚠️  Firebase initialization failed: {e}")
                print("⚠️  Falling back to API key authentication")
                self.firebase_initialized = False
    
    async def verify_firebase_token(self, authorization: Optional[str] = Header(None)) -> Dict[str, str]:
        """Verify Firebase ID token from Authorization header"""
        
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing Authorization header"
            )
        
        # Extract token from "Bearer <token>"
        try:
            scheme, token = authorization.split()
            if scheme.lower() != 'bearer':
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme"
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format"
            )
        
        # Verify token with Firebase
        if not self.firebase_initialized:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase authentication not available"
            )
        
        try:
            decoded_token = firebase_auth.verify_id_token(token)
            return {
                "user_id": decoded_token['uid'],
                "email": decoded_token.get('email', ''),
                "email_verified": decoded_token.get('email_verified', False)
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    async def verify_api_key(self, api_key: Optional[str] = Security(APIKeyHeader(name="X-API-Key", auto_error=False))) -> str:
        """Verify API key from header (fallback auth)"""
        
        # Allow unauthenticated access in development
        if os.getenv('ENVIRONMENT') == 'development':
            return "dev_user"
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing API Key"
            )
        
        if api_key not in self.api_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid API Key"
            )
        
        return api_key
    
    async def get_current_user(
        self, 
        authorization: Optional[str] = Header(None),
        api_key: Optional[str] = Security(APIKeyHeader(name="X-API-Key", auto_error=False))
    ) -> Dict[str, str]:
        """
        Get current user from either Firebase token or API key
        Tries Firebase first, falls back to API key
        """
        
        # Try Firebase token first
        if authorization and self.firebase_initialized:
            try:
                return await self.verify_firebase_token(authorization)
            except HTTPException:
                pass  # Fall through to API key
        
        # Fall back to API key
        if api_key:
            user_id = await self.verify_api_key(api_key)
            return {
                "user_id": user_id,
                "email": "",
                "email_verified": False,
                "auth_method": "api_key"
            }
        
        # Development mode
        if os.getenv('ENVIRONMENT') == 'development':
            return {
                "user_id": "dev_user",
                "email": "dev@example.com",
                "email_verified": True,
                "auth_method": "development"
            }
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        return secrets.token_urlsafe(32)


# Global instance
auth_service = AuthService()
