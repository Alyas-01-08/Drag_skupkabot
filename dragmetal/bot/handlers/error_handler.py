from aiogram.utils import exceptions
from loguru import logger

from dragmetal.bot.loader import dp


@dp.errors_handler()
async def errors_handler(update, exception):
    """
    Exceptions handler. Catches all exceptions within task factory tasks.
    :param update:
    :param exception:
    :return: stdout logger
    """

    if isinstance(exception, exceptions.CantDemoteChatCreator):
        logger.debug("Can't demote chat creator")
        return True

    if isinstance(exception, exceptions.MessageNotModified):
        logger.debug("Message is not modified")
        return True
    if isinstance(exception, exceptions.MessageCantBeDeleted):
        logger.debug("Message cant be deleted")
        return True

    if isinstance(exception, exceptions.MessageToDeleteNotFound):
        logger.debug("Message to delete not found")
        return True

    if isinstance(exception, exceptions.MessageTextIsEmpty):
        logger.debug("MessageTextIsEmpty")
        return True

    if isinstance(exception, exceptions.Unauthorized):
        logger.info(f"Unauthorized: {exception}")
        return True

    if isinstance(exception, exceptions.InvalidQueryID):
        logger.exception(f"InvalidQueryID: {exception}", update=update.to_python())
        return True

    if isinstance(exception, exceptions.TelegramAPIError):
        logger.exception(f"TelegramAPIError: {exception}", update=update.to_python())
        return True
    if isinstance(exception, exceptions.RetryAfter):
        logger.exception(f"RetryAfter: {exception}", update=update.to_python())
        return True
    if isinstance(exception, exceptions.CantParseEntities):
        logger.exception(f"CantParseEntities: {exception}", update=update.to_python())
        return True

    logger.exception(f"Не учтенная ошибка {exception}", update=update.to_python(), unknown_error=True,
                     exception=exception)
