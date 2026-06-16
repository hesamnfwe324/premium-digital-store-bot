from aiogram import Router
from .dashboard import router as dashboard_router
from .products import router as products_router
from .orders import router as orders_router
from .users import router as users_router
from .analytics import router as analytics_router
from .broadcast import router as broadcast_router
from .inventory import router as inventory_router

router = Router()
router.include_router(dashboard_router)
router.include_router(products_router)
router.include_router(orders_router)
router.include_router(users_router)
router.include_router(analytics_router)
router.include_router(broadcast_router)
router.include_router(inventory_router)
