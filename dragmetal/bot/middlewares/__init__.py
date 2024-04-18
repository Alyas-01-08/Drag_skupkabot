from aiogram import Dispatcher
from loguru import logger

from .auth import AuthMiddleware


def middlewares_setup(dp: Dispatcher):
    dp.middleware.setup(AuthMiddleware())
    logger.info(
        "Middlewares setup",
    )
