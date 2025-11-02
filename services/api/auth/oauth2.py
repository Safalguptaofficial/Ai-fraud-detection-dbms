"""
OAuth2 SSO Integration
Supports Google, Microsoft, Okta, and generic OAuth2 providers
"""
import httpx
from typing import Optional, Dict
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)


class OAuth2Provider:
    """Base OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.authorization_endpoint = ""
        self.token_endpoint = ""
        self.user_info_endpoint = ""
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth2 authorization URL"""
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": self.get_scopes(),
            "state": state
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.authorization_endpoint}?{query_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                },
                headers={"Accept": "application/json"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get user information from OAuth2 provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.user_info_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            return response.json()
    
    def get_scopes(self) -> str:
        """Get OAuth2 scopes"""
        return "openid profile email"


class GoogleOAuth(OAuth2Provider):
    """Google OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        super().__init__(client_id, client_secret, redirect_uri)
        self.authorization_endpoint = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_endpoint = "https://oauth2.googleapis.com/token"
        self.user_info_endpoint = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    def get_scopes(self) -> str:
        return "openid profile email"
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get Google user information"""
        user_data = await super().get_user_info(access_token)
        
        # Normalize to our format
        return {
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "first_name": user_data.get("given_name"),
            "last_name": user_data.get("family_name"),
            "picture": user_data.get("picture"),
            "email_verified": user_data.get("verified_email", False),
            "provider": "google",
            "provider_id": user_data.get("id")
        }


class MicrosoftOAuth(OAuth2Provider):
    """Microsoft/Azure AD OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, tenant: str = "common"):
        super().__init__(client_id, client_secret, redirect_uri)
        self.tenant = tenant
        self.authorization_endpoint = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        self.token_endpoint = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        self.user_info_endpoint = "https://graph.microsoft.com/v1.0/me"
    
    def get_scopes(self) -> str:
        return "openid profile email User.Read"
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get Microsoft user information"""
        user_data = await super().get_user_info(access_token)
        
        # Normalize to our format
        return {
            "email": user_data.get("mail") or user_data.get("userPrincipalName"),
            "name": user_data.get("displayName"),
            "first_name": user_data.get("givenName"),
            "last_name": user_data.get("surname"),
            "email_verified": True,  # Microsoft emails are pre-verified
            "provider": "microsoft",
            "provider_id": user_data.get("id")
        }


class OktaOAuth(OAuth2Provider):
    """Okta OAuth2 provider"""
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, okta_domain: str):
        super().__init__(client_id, client_secret, redirect_uri)
        self.okta_domain = okta_domain
        self.authorization_endpoint = f"https://{okta_domain}/oauth2/v1/authorize"
        self.token_endpoint = f"https://{okta_domain}/oauth2/v1/token"
        self.user_info_endpoint = f"https://{okta_domain}/oauth2/v1/userinfo"
    
    async def get_user_info(self, access_token: str) -> Dict:
        """Get Okta user information"""
        user_data = await super().get_user_info(access_token)
        
        # Normalize to our format
        return {
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "first_name": user_data.get("given_name"),
            "last_name": user_data.get("family_name"),
            "email_verified": user_data.get("email_verified", False),
            "provider": "okta",
            "provider_id": user_data.get("sub")
        }

