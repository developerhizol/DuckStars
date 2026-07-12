from .start import router as start_router
from .stars import router as stars_router
from .premium import router as premium_router
from .profile import router as profile_router
from .back import router as back_router
from .payment import cryptobot_router, ton_router, sbp_router

__all__ = [
    "start_router",
    "stars_router", 
    "premium_router",
    "profile_router",
    "back_router",
    "cryptobot_router",
    "ton_router",
    "sbp_router"
]