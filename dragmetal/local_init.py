import os

from aiogram import types
from loguru import logger

from dragmetal.bot.handlers import dp as handlers_dp
from dragmetal.bot.middlewares import middlewares_setup


async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Меню 🌐"),
    ])


async def on_startup(dp):
    logger.info("Starting bot")

    middlewares_setup(dp)
    await set_default_commands(dp)
    from dragmetal.bot.utils import on_startup_notify  # pylint: disable=import-outside-toplevel

    await on_startup_notify(dp)
    logger.info("Admins notified")


def handle():
    from aiogram import executor  # pylint: disable=import-outside-toplevel
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    logger.info("Starting bot")
    executor.start_polling(handlers_dp, on_startup=on_startup)
