from pydantic import BaseModel
from datetime import datetime

class OTPCreate(BaseModel):
    target: str  # email, phone, or username
    purpose: str  # signup, login, reset

class OTPVerify(BaseModel):
    target: str
    otp: str
    purpose: str

class OTPInDB(BaseModel):
    target: str
    otp_hash: str
    purpose: str
    attempts: int = 0
    created_at: str
    expires_at: str