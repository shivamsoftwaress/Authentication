from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\+?[1-9]\d{1,14}$')
    password: str = Field(..., min_length=6)
    role: str = Field(default="customer")  # customer or admin

class UserInDB(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    password_hash: str
    role: str = "customer"
    is_active: bool = True
    is_verified: bool = False
    created_at: str
    updated_at: str

class UserOut(BaseModel):
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: str

class UserLogin(BaseModel):
    identifier: str  # username, email, or phone
    password: str