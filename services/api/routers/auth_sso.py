"""
SSO & MFA Authentication Router
Handles OAuth2 (Google, Microsoft, Okta) and MFA setup/verification
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import logging

from auth import oauth2, mfa
from auth.oauth2 import GoogleOAuth, MicrosoftOAuth, OktaOAuth
from auth.mfa import MFAManager
from tenants import TenantManager
from middleware import get_current_tenant, get_current_user_id, require_role
from deps import get_postgres
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication", "sso", "mfa"])


# ============================================================================
# OAuth2 / SSO Endpoints
# ============================================================================

@router.get("/oauth/{provider}/authorize")
async def oauth_authorize(
    provider: str,
    redirect_uri: Optional[str] = Query(None)
):
    """
    🔐 Start OAuth2 authorization flow
    
    Supported providers: google, microsoft, okta
    """
    try:
        # Get OAuth provider
        if provider == "google":
            oauth = GoogleOAuth(
                client_id=settings.google_oauth_client_id,
                client_secret=settings.google_oauth_client_secret,
                redirect_uri=redirect_uri or f"{settings.base_url}/api/v1/auth/oauth/google/callback"
            )
        elif provider == "microsoft":
            oauth = MicrosoftOAuth(
                client_id=settings.microsoft_oauth_client_id,
                client_secret=settings.microsoft_oauth_client_secret,
                redirect_uri=redirect_uri or f"{settings.base_url}/api/v1/auth/oauth/microsoft/callback"
            )
        elif provider == "okta":
            oauth = OktaOAuth(
                client_id=settings.okta_oauth_client_id,
                client_secret=settings.okta_oauth_client_secret,
                redirect_uri=redirect_uri or f"{settings.base_url}/api/v1/auth/oauth/okta/callback",
                okta_domain=settings.okta_domain
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported OAuth provider: {provider}"
            )
        
        # Generate authorization URL
        auth_url = oauth.get_authorization_url()
        
        # Redirect to provider
        return RedirectResponse(auth_url)
        
    except Exception as e:
        logger.error(f"OAuth authorization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authorization failed"
        )


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: Optional[str] = Query(None),
    db=Depends(get_postgres)
):
    """
    🔐 OAuth2 callback endpoint
    
    Handles the redirect from OAuth provider after user authorization
    """
    try:
        # Get OAuth provider
        if provider == "google":
            oauth = GoogleOAuth(
                client_id=settings.google_oauth_client_id,
                client_secret=settings.google_oauth_client_secret,
                redirect_uri=f"{settings.base_url}/api/v1/auth/oauth/google/callback"
            )
        elif provider == "microsoft":
            oauth = MicrosoftOAuth(
                client_id=settings.microsoft_oauth_client_id,
                client_secret=settings.microsoft_oauth_client_secret,
                redirect_uri=f"{settings.base_url}/api/v1/auth/oauth/microsoft/callback"
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
        # Exchange code for token
        token_data = await oauth.exchange_code_for_token(code)
        
        # Get user info
        user_info = await oauth.get_user_info(token_data['access_token'])
        
        # Find or create user
        manager = TenantManager(db)
        
        # TODO: Link OAuth account to existing user or create new user
        # For now, return user info
        
        return {
            "success": True,
            "provider": provider,
            "user_info": user_info,
            "message": "OAuth login successful! TODO: Create JWT token and redirect to dashboard"
        }
        
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback failed: {str(e)}"
        )


# ============================================================================
# MFA Endpoints
# ============================================================================

class MFASetupResponse(BaseModel):
    secret: str
    qr_code: str
    backup_codes: list[str]


class MFAVerifyRequest(BaseModel):
    token: str


@router.post("/mfa/setup", response_model=MFASetupResponse)
async def setup_mfa(
    tenant_id: str = Depends(get_current_tenant),
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    🔒 Setup MFA (Two-Factor Authentication)
    
    Generates QR code for Google Authenticator or Authy
    """
    try:
        cursor = db.cursor()
        
        # Get user email
        cursor.execute(
            "SELECT email FROM tenant_users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_email = result[0]
        
        # Generate MFA secret
        mfa = MFAManager(issuer_name="FraudGuard")
        secret = mfa.generate_secret()
        qr_code = mfa.generate_qr_code(secret, user_email)
        backup_codes = mfa.get_backup_codes()
        
        # Store secret (not enabled yet)
        cursor.execute("""
            INSERT INTO user_mfa_secrets (user_id, secret, enabled, backup_codes)
            VALUES (%s, %s, FALSE, %s)
            ON CONFLICT (user_id) 
            DO UPDATE SET secret = %s, backup_codes = %s, updated_at = CURRENT_TIMESTAMP
        """, (user_id, secret, backup_codes, secret, backup_codes))
        
        db.commit()
        cursor.close()
        
        logger.info(f"MFA setup initiated for user {user_id}")
        
        return MFASetupResponse(
            secret=secret,
            qr_code=qr_code,
            backup_codes=backup_codes
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA setup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA setup failed"
        )


@router.post("/mfa/verify")
async def verify_mfa(
    request: MFAVerifyRequest,
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    ✅ Verify MFA token and enable MFA
    
    Verifies the 6-digit code from authenticator app
    """
    try:
        cursor = db.cursor()
        
        # Get MFA secret
        cursor.execute(
            "SELECT secret FROM user_mfa_secrets WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="MFA not setup. Please setup MFA first."
            )
        
        secret = result[0]
        
        # Verify token
        mfa = MFAManager()
        is_valid = mfa.verify_token(secret, request.token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA token"
            )
        
        # Enable MFA
        cursor.execute(
            "UPDATE user_mfa_secrets SET enabled = TRUE WHERE user_id = %s",
            (user_id,)
        )
        db.commit()
        cursor.close()
        
        logger.info(f"MFA enabled for user {user_id}")
        
        return {
            "success": True,
            "message": "MFA enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA verification failed"
        )


@router.post("/mfa/disable")
async def disable_mfa(
    request: MFAVerifyRequest,
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    🚫 Disable MFA
    
    Requires valid MFA token to disable
    """
    try:
        cursor = db.cursor()
        
        # Get MFA secret
        cursor.execute(
            "SELECT secret, enabled FROM user_mfa_secrets WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="MFA not setup")
        
        secret, enabled = result
        
        if not enabled:
            return {"success": True, "message": "MFA already disabled"}
        
        # Verify token before disabling
        mfa = MFAManager()
        is_valid = mfa.verify_token(secret, request.token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid MFA token"
            )
        
        # Disable MFA
        cursor.execute(
            "UPDATE user_mfa_secrets SET enabled = FALSE WHERE user_id = %s",
            (user_id,)
        )
        db.commit()
        cursor.close()
        
        logger.info(f"MFA disabled for user {user_id}")
        
        return {
            "success": True,
            "message": "MFA disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"MFA disable failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MFA disable failed"
        )


@router.get("/mfa/status")
async def mfa_status(
    user_id: int = Depends(get_current_user_id),
    db=Depends(get_postgres)
):
    """
    📊 Get MFA status
    """
    try:
        cursor = db.cursor()
        
        cursor.execute(
            "SELECT enabled FROM user_mfa_secrets WHERE user_id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        
        if not result:
            return {"enabled": False, "setup": False}
        
        return {"enabled": result[0], "setup": True}
        
    except Exception as e:
        logger.error(f"Failed to get MFA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get MFA status"
        )

