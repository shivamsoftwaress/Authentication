import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Tuple
from ..core.config import settings
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.redis_client = None
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def check_rate_limit(self, key: str, limit: int, window_minutes: int = 60) -> Tuple[bool, int]:
        """
        Check if rate limit is exceeded
        Returns: (is_allowed, remaining_attempts)
        """
        if not self.redis_client:
            # If Redis is not available, allow all requests
            logger.warning("Redis not available, skipping rate limit")
            return True, limit
        
        try:
            current = await self.redis_client.get(key)
            
            if current is None:
                # First request
                await self.redis_client.setex(key, window_minutes * 60, 1)
                return True, limit - 1
            
            current_count = int(current)
            
            if current_count >= limit:
                return False, 0
            
            # Increment counter
            await self.redis_client.incr(key)
            return True, limit - current_count - 1
        
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the request
            return True, limit

# Global rate limiter instance
rate_limiter = RateLimiter()