import logging

logger = logging.getLogger(__name__)

class MockEmailProvider:
    """Mock email provider that logs to console"""
    
    async def send_otp(self, email: str, otp: str, purpose: str):
        """Send OTP via email (mock - prints to console)"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📧 EMAIL OTP - {purpose.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"To: {email}")
        logger.info(f"OTP Code: {otp}")
        logger.info(f"Purpose: {purpose}")
        logger.info(f"Valid for: 5 minutes")
        logger.info(f"{'='*60}\n")
        return True

class MockSMSProvider:
    """Mock SMS provider that logs to console"""
    
    async def send_otp(self, phone: str, otp: str, purpose: str):
        """Send OTP via SMS (mock - prints to console)"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📱 SMS OTP - {purpose.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"To: {phone}")
        logger.info(f"OTP Code: {otp}")
        logger.info(f"Purpose: {purpose}")
        logger.info(f"Valid for: 5 minutes")
        logger.info(f"{'='*60}\n")
        return True

# Singleton instances
email_provider = MockEmailProvider()
sms_provider = MockSMSProvider()