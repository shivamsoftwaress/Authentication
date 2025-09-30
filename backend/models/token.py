from pydantic import BaseModel
from typing import Optional

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenInDB(BaseModel):
    user_id: str
    refresh_token_hash: str
    created_at: str
    expires_at: str
    revoked: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None