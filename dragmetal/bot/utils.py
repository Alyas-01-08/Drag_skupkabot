import asyncio
import re

from aiogram import Dispatcher
from asgiref.sync import sync_to_async
from django.conf import settings
from loguru import logger

from dragmetal.bot.loader import bot
from dragmetal.models import UserBot


async def on_startup_notify(dp: Dispatcher):
    """Уведомление разрабов о запуске бота"""

    # for admin in settings.ADMINS_BOT:
    #     try:
    #         await dp.bot.send_message(admin, "Бот Запущен")
    #     except Exception as err:
    #         logger.info(f"Admin chat_id not found or bot was blocked: {str(err)}")
    for user in await sync_to_async(UserBot.objects.all)():
        if user.is_admin:
            try:
                await dp.bot.send_message(user.id, "Бот Запущен")
            except Exception as err:
                logger.info(f"Admin chat_id not found or bot was blocked: {str(err)}")
        try:
            await dp.bot.send_message(user.id,
                                      "Бот был обновлен, для нормального функционирования бота нажмите /start")
            await asyncio.sleep(0.5)
        except Exception as err:
            logger.info(f"User chat_id not found or bot was blocked: {str(err)}")


async def on_end_notify(dp: Dispatcher):
    """Уведомление разрабов о запуске бота"""

    # for admin in settings.ADMINS_BOT:
    #     try:
    #         await dp.bot.send_message(admin, "Бот Запущен")
    #     except Exception as err:
    #         logger.info(f"Admin chat_id not found or bot was blocked: {str(err)}")
    for user in await sync_to_async(UserBot.objects.all)():
        try:
            await dp.bot.send_message(user.user_id, "Бот Остановлен, для сервисного обслуживания")
        except Exception as err:
            logger.info(f"User chat_id not found or bot was blocked: {str(err)}")


async def del_message(*args):
    """Удаление сообщения"""

    chat, message_id = args
    try:
        await bot.delete_message(chat_id=chat, message_id=message_id)
    except Exception:
        logger.exception(
            "del message error",
        )


def escape_markdown(text: str, version: int = 2, entity_type: str = None) -> str:
    """Helper function to escape telegram markup symbols.
    Args:
        text (:obj:`str`): The text.
        version (:obj:`int` | :obj:`str`): Use to specify the version of telegrams Markdown.
            Either ``1`` or ``2``. Defaults to ``1``.
        entity_type (:obj:`str`, optional): For the entity types
            :tg-const:`telegram.MessageEntity.PRE`, :tg-const:`telegram.MessageEntity.CODE` and
            the link part of :tg-const:`telegram.MessageEntity.TEXT_LINK`, only certain characters
            need to be escaped in :tg-const:`telegram.constants.ParseMode.MARKDOWN_V2`.
            See the official API documentation for details. Only valid in combination with
            ``version=2``, will be ignored else.
    """
    if int(version) == 1:
        escape_chars = r"_*`["
    elif int(version) == 2:
        if entity_type in ["pre", "code"]:
            escape_chars = r"\`"
        elif entity_type == "text_link":
            escape_chars = r"\)"
        else:
            escape_chars = r"_[]()~`>#+-=|{}.!"
    else:
        raise ValueError("Markdown version must be either 1 or 2!")

    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)
