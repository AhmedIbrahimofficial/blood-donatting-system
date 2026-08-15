"""
Rate limiting via slowapi (uses in-memory storage — swap to Redis in prod).

Limits:
  - Auth endpoints  : 10 requests / minute  per IP
  - General API     : 100 requests / minute per IP
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Tests mein rate limiting disable — conftest ENVIRONMENT=test set karta hai
import os
_default_limits = [] if os.environ.get("ENVIRONMENT") == "test" else ["100/minute"]

limiter = Limiter(key_func=get_remote_address, default_limits=_default_limits)
