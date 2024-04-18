from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message, CallbackQuery


class Button(BoundFilter):
    """
    Фильтр для обработки кнопок в клавиатуре
    """

    def __init__(self, key, contains=False):  # pylint: disable=invalid-overridden-method
        self.key = key
        self.contains = contains

    async def check(self, message) -> bool:
        if isinstance(message, Message):
            if self.contains:
                return self.key in message.text
            else:
                return message.text == self.key
        elif isinstance(message, CallbackQuery):
            if message.data.startswith("menu_back") and self.key == "menu_back":
                pass
            if self.contains:
                return self.key in message.data
            else:
                return self.key == message.data
