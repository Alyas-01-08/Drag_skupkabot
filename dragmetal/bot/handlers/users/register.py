from pprint import pprint

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import ContentType
from aiogram.utils import markdown as md

from dragmetal.bot.filters.hendlers_filters import Button
from dragmetal.bot.keyboards.menu import btn_user_type, btn_privacy_user
from dragmetal.bot.loader import dp
from dragmetal.bot.states import PhysicalData, EntityData
from dragmetal.services import create_user, state_reset
from django.conf import settings
from utils.validate import validate_email


@dp.callback_query_handler(Button('register'), state="*")
@dp.async_task
async def start_register(call: types.CallbackQuery):
    """Стратегия для продолжения регистрации"""
    await call.answer()
    await call.message.edit_text("Выберите тип пользователя:", reply_markup=btn_user_type)


@dp.callback_query_handler(Button('physical'), state="*")
@dp.async_task
async def physical_register(call: types.CallbackQuery, state: FSMContext):
    """Стратегия для продолжения регистрации - Физических лиц"""
    await call.message.edit_text("Введите Ваше имя:")
    await state.update_data(user_type="Физ. лицо")
    await PhysicalData.f_name.set()


@dp.callback_query_handler(Button('entity'), state="*")
@dp.async_task
async def entity_register(call: types.CallbackQuery, state: FSMContext):
    """Стратегия для продолжения регистрации - Юридических лиц"""
    await call.message.edit_text("Введите ИНН:")
    await state.update_data(user_type="Юр. лицо")
    await EntityData.pin.set()


@dp.message_handler(state=EntityData.pin)
async def accept_pin(message: types.Message, state: FSMContext):
    await state.update_data(pin=message.text)
    await message.answer("Введите ОГРН/ОГРНИП:")
    await EntityData.ogrn.set()


@dp.message_handler(state=EntityData.ogrn)
async def accept_ogrn(message: types.Message, state: FSMContext):
    await state.update_data(ogrn=message.text)
    await message.answer("Введите расчетный счет:")
    await EntityData.payment_account.set()


@dp.message_handler(state=EntityData.payment_account)
async def accept_payment_account(message: types.Message, state: FSMContext):
    await state.update_data(payment_account=message.text)
    await message.answer("Введите Ваше имя:")
    await EntityData.f_name.set()


@dp.message_handler(state=[EntityData.f_name, PhysicalData.f_name])
async def accept_f_name_entity(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await message.answer("Введите Вашу фамилию:")
    if (await state.get_state()).startswith('EntityData'):
        await EntityData.l_name.set()
    else:
        await PhysicalData.l_name.set()


@dp.message_handler(state=[EntityData.l_name, PhysicalData.l_name])
async def accept_l_name_entity(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.answer("Укажите Ваш номер телефона:")
    if (await state.get_state()).startswith('EntityData'):
        await EntityData.phone.set()
    else:
        await PhysicalData.phone.set()


@dp.message_handler(state=[EntityData.phone, PhysicalData.phone])
async def accept_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone_number=message.text)

    if (await state.get_state()).startswith('EntityData'):
        await message.answer("Укажите Ваш email адрес:")
        await EntityData.email.set()
    else:
        await message.answer("Отправьте фото вашего паспорта:")
        await PhysicalData.passport.set()


@dp.message_handler(state=EntityData.email)
async def accept_email(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Укажите адрес город:")
    await EntityData.city.set()


@dp.message_handler(state=EntityData.city)
async def accept_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Укажите адрес места скупки:")
    await EntityData.address.set()


@dp.message_handler(state=PhysicalData.passport, content_types=ContentType.PHOTO)
async def accept_passport(message: types.Message, state: FSMContext):
    photo_path = f'media/passport/{message.from_user.id}.jpg'
    await message.photo[0].download(destination_file=photo_path)
    await state.update_data(passport=photo_path)
    await message.answer(
        md.link('Пользовательское соглашение Drag_skupka и политика конфиденциальности\.',
                'https://www.google.ru/'), reply_markup=btn_privacy_user)


@dp.message_handler(state=EntityData.address)
async def accept_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer(
        md.link('Пользовательское соглашение Drag_skupka и политика конфиденциальности\.',
                'https://www.google.ru/'), reply_markup=btn_privacy_user)


@dp.callback_query_handler(Button('privacy'), state=[PhysicalData.passport, EntityData.address])
async def accept_privacy(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await create_user(data, call.message.message_id)
    await call.answer("Поздравляем, регистрация успешно завершена! Меню будет доступно в течение нескольких минут")
    await state_reset(state)
