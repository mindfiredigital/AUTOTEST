"""
Rate limiter singleton — shared across app.py and routers.

Keeping it in its own module avoids the circular import that would occur
if routers imported `limiter` directly from `app.app` (which in turn
includes those routers).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
