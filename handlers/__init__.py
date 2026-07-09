# handlers/__init__.py
from .start import router as start_router
from .stars import router as stars_router
from .premium import router as premium_router
from .gifts import router as gifts_router
from .profile import router as profile_router
from .payment import router as payment_router
from .back import router as back_router

__all__ = [
    "start_router",
    "stars_router", 
    "premium_router",
    "gifts_router",
    "profile_router",
    "payment_router",
    "back_router"
]