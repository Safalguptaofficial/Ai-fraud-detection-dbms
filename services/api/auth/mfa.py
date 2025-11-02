"""
Multi-Factor Authentication (MFA) Implementation
Supports TOTP (Google Authenticator, Authy) and SMS
"""
import pyotp
import qrcode
import io
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class MFAManager:
    """Manages MFA setup and verification"""
    
    def __init__(self, issuer_name: str = "FraudGuard"):
        self.issuer_name = issuer_name
    
    def generate_secret(self) -> str:
        """Generate a new MFA secret for a user"""
        return pyotp.random_base32()
    
    def get_provisioning_uri(self, secret: str, user_email: str) -> str:
        """Generate provisioning URI for QR code"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(
            name=user_email,
            issuer_name=self.issuer_name
        )
    
    def generate_qr_code(self, secret: str, user_email: str) -> str:
        """Generate QR code as base64 image"""
        uri = self.get_provisioning_uri(secret, user_email)
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify MFA token
        
        Args:
            secret: User's MFA secret
            token: 6-digit code from authenticator app
            window: Time window for validation (default 30 seconds)
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception as e:
            logger.error(f"MFA verification failed: {e}")
            return False
    
    def get_backup_codes(self, count: int = 10) -> list[str]:
        """Generate backup codes for account recovery"""
        return [pyotp.random_base32()[:8] for _ in range(count)]


class SMSMFAManager:
    """SMS-based MFA (for future implementation)"""
    
    def __init__(self, twilio_sid: Optional[str] = None, twilio_token: Optional[str] = None):
        self.twilio_sid = twilio_sid
        self.twilio_token = twilio_token
    
    async def send_code(self, phone_number: str) -> str:
        """
        Send SMS code to phone number
        Returns: code that was sent
        """
        # Generate 6-digit code
        code = pyotp.random_base32()[:6].upper()
        
        # TODO: Integrate with Twilio
        # from twilio.rest import Client
        # client = Client(self.twilio_sid, self.twilio_token)
        # message = client.messages.create(
        #     body=f"Your FraudGuard verification code is: {code}",
        #     from_="+1234567890",
        #     to=phone_number
        # )
        
        logger.info(f"SMS MFA code sent to {phone_number}: {code}")
        return code
    
    def verify_code(self, sent_code: str, user_code: str) -> bool:
        """Verify SMS code"""
        return sent_code.upper() == user_code.upper()

