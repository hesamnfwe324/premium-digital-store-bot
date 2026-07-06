from aiogram import Router
from .start import router as start_router
from .language import router as language_router
from .home import router as home_router
from .products import router as products_router
from .orders import router as orders_router
from .account import router as account_router
from .payment import router as payment_router
from .wallet import router as wallet_router
from .support import router as support_router
from .deals import router as deals_router
from .reviews import router as reviews_router
from .loyalty import router as loyalty_router
from .admin import router as admin_router

def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(language_router)
    main_router.include_router(home_router)
    main_router.include_router(products_router)
    main_router.include_router(orders_router)
    main_router.include_router(account_router)
    main_router.include_router(payment_router)
    main_router.include_router(wallet_router)
    main_router.include_router(support_router)
    main_router.include_router(deals_router)
    main_router.include_router(reviews_router)
    main_router.include_router(loyalty_router)
    main_router.include_router(admin_router)
    return main_router
