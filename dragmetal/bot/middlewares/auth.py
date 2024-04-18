from aiogram import types, Dispatcher
from aiogram.dispatcher.handler import CancelHandler

from aiogram.dispatcher.middlewares import BaseMiddleware
from asgiref.sync import sync_to_async
from loguru import logger

from Drag_skupkabot import settings
from dragmetal.models import UserBot


class AuthMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict):
        logger.info(message)
        if not message.text:
            return
        if message.text.startswith('/start'):
            user, created = await sync_to_async(UserBot.get_user_and_created)(message.from_user)
            if created:
                if message.from_user.id in settings.ADMINS_BOT:
                    user.is_admin = True
                user.is_accepted = True
                user.save()
                await data['state'].update_data(user_profile=user)
            else:
                await data['state'].update_data(user_profile=user)
