"""JWT token validation for Supabase authentication."""
import jwt
from datetime import datetime
from typing import Dict, Optional
from fastapi import HTTPException, status

from app.config import settings


class JWTValidator:
    """Validate and decode Supabase JWT tokens."""
    
    def __init__(self):
        self.jwt_secret = settings.supabase_jwt_secret
        self.algorithms = ["HS256"]
    
    def decode_token(self, token: str) -> Dict:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=self.algorithms,
                options={"verify_exp": True}
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def extract_user_id(self, token: str) -> str:
        """
        Extract user ID from JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            User ID (Supabase auth UID)
        """
        payload = self.decode_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )
        
        return user_id
    
    def verify_token(self, token: str) -> bool:
        """
        Verify if token is valid.
        
        Args:
            token: JWT token string
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.decode_token(token)
            return True
        except HTTPException:
            return False


# Global JWT validator instance
jwt_validator = JWTValidator()
