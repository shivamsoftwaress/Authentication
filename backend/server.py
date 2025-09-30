from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, List

# Import models
from models.user import UserCreate, UserInDB, UserOut, UserLogin
from models.otp import OTPCreate, OTPVerify
from models.token import TokenResponse, RefreshTokenRequest

# Import core
from core.config import settings
from core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, hash_token
)

# Import services
from services.otp_service import OTPService
from services.rate_limiter import rate_limiter

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize services
otp_service = OTPService(db)

# Create the main app without a prefix
app = FastAPI(title="Authentication System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Dependency to get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        if not user.get("is_active"):
            raise HTTPException(status_code=403, detail="User account is inactive")
        
        return user
    
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency to ensure user is admin"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@api_router.post("/auth/signup", status_code=status.HTTP_201_CREATED)
async def signup(user_data: UserCreate, request: Request):
    """
    Step 1: User registration
    Creates user account and sends verification OTP
    """
    try:
        # Check rate limit
        ip = request.client.host
        allowed, remaining = await rate_limiter.check_rate_limit(
            f"signup:{ip}",
            limit=5,
            window_minutes=60
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many signup attempts. Please try again later."
            )
        
        # Check if username already exists
        existing_user = await db.users.find_one({"username": user_data.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists (if provided)
        if user_data.email:
            existing_email = await db.users.find_one({"email": user_data.email})
            if existing_email:
                raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if phone already exists (if provided)
        if user_data.phone:
            existing_phone = await db.users.find_one({"phone": user_data.phone})
            if existing_phone:
                raise HTTPException(status_code=400, detail="Phone already registered")
        
        # Hash password
        password_hash = hash_password(user_data.password)
        
        # Create user document
        now = datetime.now(timezone.utc).isoformat()
        user_doc = {
            "username": user_data.username,
            "password_hash": password_hash,
            "role": user_data.role,
            "is_active": True,
            "is_verified": False,  # Will be set to True after OTP verification
            "created_at": now,
            "updated_at": now
        }
        
        # Only add email and phone if provided (avoid null values in sparse indexes)
        if user_data.email:
            user_doc["email"] = user_data.email
        if user_data.phone:
            user_doc["phone"] = user_data.phone
        
        # Insert user
        result = await db.users.insert_one(user_doc)
        
        # Send OTP for verification
        target = user_data.email or user_data.phone or user_data.username
        target_type = "email" if user_data.email else "phone" if user_data.phone else "username"
        
        success, message = await otp_service.create_and_send_otp(target, "signup", target_type)
        
        if not success:
            # Rollback user creation if OTP sending fails
            await db.users.delete_one({"_id": result.inserted_id})
            raise HTTPException(status_code=500, detail=message)
        
        return {
            "message": "User created successfully. Please verify your account with the OTP sent.",
            "username": user_data.username,
            "target": target,
            "verification_required": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


@api_router.post("/auth/verify-signup")
async def verify_signup(otp_data: OTPVerify):
    """
    Step 2: Verify signup OTP
    Activates user account after successful OTP verification
    """
    try:
        # Verify OTP
        success, message = await otp_service.verify_otp(
            otp_data.target,
            otp_data.otp,
            otp_data.purpose
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Mark user as verified
        # Find user by email, phone, or username
        user = await db.users.find_one({
            "$or": [
                {"email": otp_data.target},
                {"phone": otp_data.target},
                {"username": otp_data.target}
            ]
        })
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user verification status
        await db.users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "is_verified": True,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        
        return {
            "message": "Account verified successfully. You can now login.",
            "verified": True
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verify signup error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")


@api_router.post("/auth/login/password")
async def login_password(login_data: UserLogin, request: Request):
    """
    Step 1 of Login: Verify password
    If password is correct, send 2FA OTP
    """
    try:
        # Check rate limit
        ip = request.client.host
        allowed, remaining = await rate_limiter.check_rate_limit(
            f"login:{ip}",
            limit=settings.RATE_LIMIT_LOGIN_PER_HOUR,
            window_minutes=60
        )
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts. Please try again later."
            )
        
        # Find user by username, email, or phone
        user = await db.users.find_one({
            "$or": [
                {"username": login_data.identifier},
                {"email": login_data.identifier},
                {"phone": login_data.identifier}
            ]
        })
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is verified
        if not user.get("is_verified"):
            raise HTTPException(
                status_code=403,
                detail="Account not verified. Please verify your account first."
            )
        
        # Verify password
        if not verify_password(login_data.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Send 2FA OTP
        target = user.get("email") or user.get("phone") or user.get("username")
        target_type = "email" if user.get("email") else "phone" if user.get("phone") else "username"
        
        success, message = await otp_service.create_and_send_otp(target, "login", target_type)
        
        if not success:
            raise HTTPException(status_code=500, detail=message)
        
        return {
            "message": "Password verified. Please enter the OTP sent to your registered contact.",
            "target": target,
            "otp_required": True,
            "username": user["username"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login password error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@api_router.post("/auth/login/verify-otp", response_model=TokenResponse)
async def login_verify_otp(otp_data: OTPVerify, response: Response, request: Request):
    """
    Step 2 of Login: Verify 2FA OTP and issue tokens
    """
    try:
        # Verify OTP
        success, message = await otp_service.verify_otp(
            otp_data.target,
            otp_data.otp,
            "login"
        )
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        # Find user
        user = await db.users.find_one({
            "$or": [
                {"email": otp_data.target},
                {"phone": otp_data.target},
                {"username": otp_data.target}
            ]
        })
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create tokens
        access_token = create_access_token({"sub": user["username"], "role": user["role"]})
        refresh_token = create_refresh_token({"sub": user["username"]})
        
        # Store refresh token hash
        now = datetime.now(timezone.utc)
        refresh_token_doc = {
            "user_id": user["username"],
            "refresh_token_hash": hash_token(refresh_token),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
            "revoked": False,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent", "")
        }
        await db.refresh_tokens.insert_one(refresh_token_doc)
        
        # Set refresh token as httpOnly cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login verify OTP error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@api_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_tokens(refresh_data: RefreshTokenRequest, response: Response):
    """Refresh access token using refresh token"""
    try:
        token = refresh_data.refresh_token
        
        # Decode token
        payload = decode_token(token)
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        username = payload.get("sub")
        
        # Check if refresh token exists and is not revoked
        token_hash = hash_token(token)
        stored_token = await db.refresh_tokens.find_one({
            "user_id": username,
            "refresh_token_hash": token_hash,
            "revoked": False
        })
        
        if not stored_token:
            raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")
        
        # Check if expired
        expires_at = datetime.fromisoformat(stored_token["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        
        # Get user
        user = await db.users.find_one({"username": username})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Create new tokens
        new_access_token = create_access_token({"sub": user["username"], "role": user["role"]})
        new_refresh_token = create_refresh_token({"sub": user["username"]})
        
        # Revoke old refresh token
        await db.refresh_tokens.update_one(
            {"_id": stored_token["_id"]},
            {"$set": {"revoked": True}}
        )
        
        # Store new refresh token
        now = datetime.now(timezone.utc)
        new_refresh_token_doc = {
            "user_id": user["username"],
            "refresh_token_hash": hash_token(new_refresh_token),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat(),
            "revoked": False
        }
        await db.refresh_tokens.insert_one(new_refresh_token_doc)
        
        # Update cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        raise HTTPException(status_code=401, detail="Could not refresh token")


@api_router.post("/auth/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    response: Response,
    user: dict = Depends(get_current_user)
):
    """Logout user by revoking refresh token"""
    try:
        token_hash = hash_token(refresh_data.refresh_token)
        
        # Revoke refresh token
        await db.refresh_tokens.update_many(
            {
                "user_id": user["username"],
                "refresh_token_hash": token_hash
            },
            {"$set": {"revoked": True}}
        )
        
        # Clear cookie
        response.delete_cookie(key="refresh_token")
        
        return {"message": "Logged out successfully"}
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(status_code=500, detail="Logout failed")


# ============================================================================
# USER ENDPOINTS
# ============================================================================

@api_router.get("/users/me", response_model=UserOut)
async def get_current_user_info(user: dict = Depends(get_current_user)):
    """Get current user information"""
    return UserOut(
        username=user["username"],
        email=user.get("email"),
        phone=user.get("phone"),
        role=user["role"],
        is_active=user["is_active"],
        is_verified=user["is_verified"],
        created_at=user["created_at"]
    )


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@api_router.get("/admin/users", response_model=List[UserOut])
async def get_all_users(admin: dict = Depends(get_current_admin)):
    """Admin: Get all users"""
    try:
        users = await db.users.find().to_list(1000)
        return [
            UserOut(
                username=user["username"],
                email=user.get("email"),
                phone=user.get("phone"),
                role=user["role"],
                is_active=user["is_active"],
                is_verified=user["is_verified"],
                created_at=user["created_at"]
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Get users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users")


@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_current_admin)):
    """Admin: Get system statistics"""
    try:
        total_users = await db.users.count_documents({})
        verified_users = await db.users.count_documents({"is_verified": True})
        admin_users = await db.users.count_documents({"role": "admin"})
        customer_users = await db.users.count_documents({"role": "customer"})
        
        return {
            "total_users": total_users,
            "verified_users": verified_users,
            "admin_users": admin_users,
            "customer_users": customer_users
        }
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")


# ============================================================================
# CUSTOMER ENDPOINTS
# ============================================================================

@api_router.get("/customer/profile", response_model=UserOut)
async def get_customer_profile(user: dict = Depends(get_current_user)):
    """Customer: Get own profile"""
    if user["role"] != "customer":
        raise HTTPException(status_code=403, detail="Customer access required")
    
    return UserOut(
        username=user["username"],
        email=user.get("email"),
        phone=user.get("phone"),
        role=user["role"],
        is_active=user["is_active"],
        is_verified=user["is_verified"],
        created_at=user["created_at"]
    )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@api_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# STARTUP/SHUTDOWN EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting application...")
    
    # Connect to Redis
    await rate_limiter.connect()
    
    # Create indexes
    try:
        await db.users.create_index("username", unique=True)
        await db.users.create_index("email", unique=True, sparse=True)
        await db.users.create_index("phone", unique=True, sparse=True)
        
        # TTL index for OTPs (auto-delete expired OTPs)
        await db.otps.create_index("expires_at", expireAfterSeconds=0)
        
        # Index for refresh tokens
        await db.refresh_tokens.create_index("user_id")
        await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Index creation warning (may already exist): {e}")
    
    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")
    
    # Close Redis connection
    await rate_limiter.close()
    
    # Close MongoDB connection
    client.close()
    
    logger.info("Application shut down successfully")
