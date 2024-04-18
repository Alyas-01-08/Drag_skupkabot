from aiogram.dispatcher.filters.state import StatesGroup, State


class PhysicalData(StatesGroup):
    f_name = State()
    l_name = State()
    phone = State()
    passport = State()


class EntityData(StatesGroup):
    pin = State()
    ogrn = State()
    payment_account = State()
    f_name = State()
    l_name = State()
    phone = State()
    email = State()
    city = State()
    address = State()


class ProductData(StatesGroup):
    type = State()
    sample = State()
    weight = State()
    address = State()
    date_time = State()
