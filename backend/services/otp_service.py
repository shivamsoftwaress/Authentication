from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..core.security import generate_otp, hash_otp, verify_otp_hash
from ..core.config import settings
from .mock_providers import email_provider, sms_provider
import logging

logger = logging.getLogger(__name__)

class OTPService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.otps
    
    async def create_and_send_otp(self, target: str, purpose: str, target_type: str = "email") -> Tuple[bool, str]:
        """
        Generate OTP, store it hashed, and send via appropriate channel
        target_type: email, phone, or username
        """
        try:
            # Generate OTP
            otp = generate_otp()
            otp_hash = hash_otp(otp)
            
            # Store OTP
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            
            otp_doc = {
                "target": target,
                "otp_hash": otp_hash,
                "purpose": purpose,
                "attempts": 0,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat()
            }
            
            # Delete any existing OTPs for this target and purpose
            await self.collection.delete_many({"target": target, "purpose": purpose})
            
            # Insert new OTP
            await self.collection.insert_one(otp_doc)
            
            # Send OTP via appropriate channel
            if target_type == "email" or "@" in target:
                await email_provider.send_otp(target, otp, purpose)
            elif target_type == "phone" or target.startswith("+"):
                await sms_provider.send_otp(target, otp, purpose)
            else:
                # If username, we need to look up user's email/phone
                # For now, just log to console
                logger.info(f"OTP for {target}: {otp}")
            
            return True, "OTP sent successfully"
        
        except Exception as e:
            logger.error(f"Error creating/sending OTP: {e}")
            return False, f"Failed to send OTP: {str(e)}"
    
    async def verify_otp(self, target: str, otp: str, purpose: str) -> Tuple[bool, str]:
        """Verify OTP against stored hash"""
        try:
            # Find OTP document
            otp_doc = await self.collection.find_one({
                "target": target,
                "purpose": purpose
            })
            
            if not otp_doc:
                return False, "No OTP found for this target"
            
            # Check if expired
            expires_at = datetime.fromisoformat(otp_doc["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                await self.collection.delete_one({"_id": otp_doc["_id"]})
                return False, "OTP has expired"
            
            # Check attempts
            if otp_doc["attempts"] >= settings.OTP_MAX_ATTEMPTS:
                await self.collection.delete_one({"_id": otp_doc["_id"]})
                return False, "Maximum OTP attempts exceeded"
            
            # Verify OTP
            if verify_otp_hash(otp, otp_doc["otp_hash"]):
                # OTP is correct, delete it
                await self.collection.delete_one({"_id": otp_doc["_id"]})
                return True, "OTP verified successfully"
            else:
                # Increment attempts
                await self.collection.update_one(
                    {"_id": otp_doc["_id"]},
                    {"$inc": {"attempts": 1}}
                )
                remaining = settings.OTP_MAX_ATTEMPTS - (otp_doc["attempts"] + 1)
                return False, f"Invalid OTP. {remaining} attempts remaining"
        
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return False, f"Failed to verify OTP: {str(e)}"