import asyncio
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import settings
from database.connection import init_db
from bot.handlers import setup_routers
from bot.middlewares import LanguageMiddleware, AntiSpamMiddleware, AdminCheckMiddleware
from bot.utils.logger import logger

os.makedirs("logs", exist_ok=True)


async def on_startup(bot: Bot) -> None:
    await init_db()
    if settings.WEBHOOK_ENABLED:
        await bot.set_webhook(
            url=settings.webhook_url,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=False,
        )
        logger.info(f"Webhook set: {settings.webhook_url}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Running in polling mode")

    bot_info = await bot.get_me()
    logger.info(f"Bot started: @{bot_info.username} (ID: {bot_info.id})")


async def on_shutdown(bot: Bot) -> None:
    logger.info("Bot is shutting down...")
    # Do NOT delete webhook on shutdown — Render free tier restarts/sleeps the service
    # and deleting the webhook would break Telegram delivery until next full restart.
    await bot.session.close()


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "app": settings.APP_NAME,
        "version": "1.0.0",
    })


def _build_dispatcher() -> Dispatcher:
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.update.middleware(LanguageMiddleware())
    dp.update.middleware(AntiSpamMiddleware())
    dp.message.middleware(AdminCheckMiddleware())

    main_router = setup_routers()
    dp.include_router(main_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    return dp


def create_webhook_app() -> tuple[web.Application, Bot, Dispatcher]:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = _build_dispatcher()

    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_get("/", health_handler)

    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=settings.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    return app, bot, dp


async def run_polling() -> None:
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = _build_dispatcher()
    await dp.start_polling(bot, allowed_updates=["message", "callback_query", "inline_query"])


def run_webhook() -> None:
    app, bot, dp = create_webhook_app()
    web.run_app(
        app,
        host="0.0.0.0",
        port=settings.WEBHOOK_PORT,
        access_log=None,
    )


if __name__ == "__main__":
    try:
        if settings.WEBHOOK_ENABLED:
            logger.info(f"Starting in WEBHOOK mode on port {settings.WEBHOOK_PORT}")
            run_webhook()
        else:
            logger.info("Starting in POLLING mode")
            asyncio.run(run_polling())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)
