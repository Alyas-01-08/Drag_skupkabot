import asyncio
import os

from aiogram import types
from aiogram.utils.executor import start_webhook
from loguru import logger

from dragmetal.bot.handlers import dp as handlers_dp
from dragmetal.bot.middlewares import middlewares_setup


WEBHOOK_HOST = "https://smartgift.space"
WEBHOOK_PATH = "/botwebhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Меню 🌐"),
    ])


async def on_startup(dp):
    logger.info("Starting bot")

    middlewares_setup(dp)
    await set_default_commands(dp)
    from dragmetal.bot.utils import on_startup_notify  # pylint: disable=import-outside-toplevel

    await dp.bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook setup")
    asyncio.create_task(on_startup_notify(dp))
    logger.info("Admins notified")


async def on_shutdown(dp):
    logger.warning("Shutting down..")
    from dragmetal.bot.utils import on_end_notify
    # insert code here to run it before shutdown
    asyncio.create_task(on_end_notify(dp))
    # Remove webhook (not acceptable in some cases)
    await dp.bot.delete_webhook()

    # Close DB connection (if used)
    await dp.storage.close()
    await dp.storage.wait_closed()

    logger.warning("Bye!")


def handle():
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    logger.info("Starting bot")
    web_app_host = "0.0.0.0"  # or ip
    web_app_port = 3033

    logger.info("Starting webhook bot")
    start_webhook(
        dispatcher=handlers_dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=web_app_host,
        port=web_app_port)
