from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.builtin import CommandStart
from asgiref.sync import sync_to_async
from loguru import logger
from decimal import Decimal, InvalidOperation

from dragmetal.models import UserBot
from dragmetal.bot.filters.hendlers_filters import Button
from dragmetal.bot.keyboards import menu
from dragmetal.bot.keyboards.menu import btn_menu, btn_create_user, btn_add_menu, btn_add_rm_menu, btn_metal_menu, \
    btn_samples, btn_confirm, btn_menu_back, btn_users_metal, btn_users_sample, btn_ordering, geo_markup
from dragmetal.bot.loader import dp, bot
from dragmetal.bot.utils import escape_markdown
from dragmetal.services import get_info, convert_slug_to_name, get_sample_obj, manage_stock, state_reset, \
    weight_in_sell_chak, basket_reject
from dragmetal.bot.states import ProductData


@dp.message_handler(CommandStart(), state="*")
async def bot_start(message: types.Message, state: FSMContext):
    """Обработка команды /start"""
    logger.info("Пользователь {} нажал на кнопку /start".format(message.from_user.id))
    data = await state.get_data()
    user_profile = data.get('user_profile')
    if not user_profile.privacy:
        await message.answer("Начнем регистрацию:", reply_markup=btn_create_user)
    else:
        await message.answer('Добро пожаловать в главное меню', reply_markup=btn_menu)
        await state_reset(state)

#
# @dp.message_handler(commands=['help'], state="*")
# async def bot_help(message: types.Message, state: FSMContext):
#     """Обработка команды /help"""
#     await bot.send_message(message.from_user.id, text='Нажмите на кнопку чтобы получить вашу геолокацию',
#                            reply_markup=geo_markup)
#
#
# @dp.message_handler(content_types=types.ContentType.LOCATION, state="*")
# async def gis(message: types.Message, state: FSMContext):
#     logger.info("Пользователь {} нажал на кнопку gis".format(message.from_user.id))
#     print(message)
#     await message.delete_reply_markup()


@dp.callback_query_handler(Button('menu'), state="*")
async def menu(call: types.CallbackQuery, state: FSMContext):
    logger.info("Пользователь {} нажал на кнопку /start".format(call.from_user.id))
    await call.message.edit_reply_markup()
    await bot.send_message(call.from_user.id, text='Главное меню', reply_markup=btn_menu)
    data = await state.get_data()
    user = data.get('user_profile')
    await state_reset(state)
    await basket_reject(user)
    print(data)


@dp.callback_query_handler(Button('stock'), state="*")
@dp.callback_query_handler(Button('calculator'), state="*")
async def stock_count(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки Склад/Калькулятор"""
    if call.data == 'calculator':
        logger.info("Пользователь {} нажал на кнопку Калькулятор".format(call.from_user.id))
        return await call.message.edit_text("Что будем считать?", parse_mode='html',
                                            reply_markup=btn_metal_menu('count'))
    logger.info("Пользователь {} нажал на кнопку Склад".format(call.from_user.id))
    data = await state.get_data()
    user_profile: UserBot = data.get('user_profile')
    text = "<b>****СКЛАД****</b>\n"
    if user_profile.users_stock.all():
        new_text = await get_info(text=text, model=user_profile)
        btn = btn_add_rm_menu
    else:
        new_text = text + "<i>В складе пока ничего нет.</i>\n\nДобавьте что-нибудь"
        btn = btn_add_menu

    await call.message.edit_text(new_text, parse_mode='html', reply_markup=btn)


@dp.callback_query_handler(lambda call: call.data == 'add' or call.data == 'remove', state="*")
async def add_to_stock(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки добавить в Склад/удалить из Склада"""
    await call.message.edit_reply_markup()
    await state.update_data(type=call.data)
    data = await state.get_data()
    print(call.data)
    if call.data == 'add':
        logger.info("Пользователь {} нажал на кнопку добавить в Склад".format(call.from_user.id))
        text = "Что добавим?"
        btn = btn_metal_menu('add')
    else:
        logger.info("Пользователь {} нажал на кнопку удалить со Склада".format(call.from_user.id))
        text = "Что удалим?"
        btn = btn_users_metal(data.get('user_profile'), 'remove')
    await bot.send_message(call.from_user.id, text=text, reply_markup=btn)
    await ProductData.type.set()


@dp.callback_query_handler(Button('add-', True), state=ProductData.type)
@dp.callback_query_handler(Button('remove-', True), state=ProductData.type)
@dp.callback_query_handler(Button('count-', True), state="*")
async def add_metal(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки добавления/удаления/расчета того или иного металла"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    metal_name = await convert_slug_to_name(call.data)
    data = await state.get_data()
    print(call.data)
    await state.update_data(call_back_metal=call.data)
    await state.update_data(metal_name=metal_name)
    btn = btn_users_sample(data.get('user_profile'), call.data, 'remove') if call.data.startswith('remove') \
        else btn_samples(call.data, call.data.split('-')[0])
    await call.message.edit_text("Какой пробы?", reply_markup=btn)
    await ProductData.sample.set()


@dp.callback_query_handler(Button('-add', True), state=ProductData.sample)
@dp.callback_query_handler(Button('-remove', True), state=ProductData.sample)
@dp.callback_query_handler(Button('-count', True), state=ProductData.sample)
@dp.callback_query_handler(Button('-sell', True), state=ProductData.sample)
async def add_metals_sample(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки Пробы"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    sample = call.data.split('-')[0]
    data = await state.get_data()
    print(sample)
    instance = get_sample_obj(data.get('metal_name'), sample)
    await state.update_data(sample_instance=instance)
    await state.update_data(call_text_sample=sample)
    await call.message.edit_text(text="Сколько граммов?")
    await ProductData.weight.set()


@dp.message_handler(state=ProductData.weight)
async def add_result(message: types.Message, state: FSMContext):
    """Обработка граммовки"""
    logger.info("Пользователь {} ввел граммовку".format(message.from_user.id))
    try:
        data = await state.get_data()
        d = Decimal(message.text)
        if data.get('type') in ['add', 'remove']:
            text = "Вы хотите добавить в свой Склад " if data['type'] == 'add' else "Вы хотите удалить со Склада "
            btn = btn_confirm
        elif data.get('type') == 'sell':
            if weight_in_sell_chak(data, d):
                text = "На вашем складе отсутствует необходимое количество данного металла. Пополните для начало склад."
                return await message.answer(text=text, reply_markup=btn_menu_back, parse_mode='html')
            text = "Вы хотите продать"
            btn = btn_ordering
        else:
            sample = data.get('sample_instance')
            text = f"{d} грамма {data['metal_name']} - {data['call_text_sample']}-й пробы стоит {sample.price * d}₽"
            await state_reset(state)
            return await message.answer(text, reply_markup=btn_menu_back, parse_mode='html')
        text += f" {d} грамма {data['metal_name']} - {data['call_text_sample']}-й пробы"
        await state.update_data(weight=d)
        await message.answer(text, reply_markup=btn, parse_mode='html')
    except InvalidOperation:
        await message.answer(text="Введите пожалуйста числовое значение или число с плавающей точкой (1, 0.58 и т.д.)",
                             reply_markup=btn_menu_back, parse_mode='html')


@dp.callback_query_handler(Button('confirm'), state=ProductData.weight)
async def add_confirm(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    await manage_stock(data)
    await call.message.edit_text("Операция выполнена успешно.", reply_markup=btn_menu_back, parse_mode='html')
    await state_reset(state)
    print(data)
