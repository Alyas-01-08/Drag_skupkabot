from aiogram import types
from aiogram.dispatcher import FSMContext
from loguru import logger
from decimal import Decimal, InvalidOperation

from dragmetal.models import UserBot
from dragmetal.bot.filters.hendlers_filters import Button
from dragmetal.bot.keyboards.menu import btn_menu, btn_create_user, btn_add_menu, btn_add_rm_menu, btn_metal_menu, \
    btn_samples, btn_confirm, btn_menu_back, btn_users_metal, btn_users_sample, btn_stock, btn_order_complete, \
    btn_basket_continue
from dragmetal.bot.loader import dp, bot
from dragmetal.services import get_info, convert_slug_to_name, get_sample_obj, manage_stock, users_stock_chak, \
    new_basket_create, order_complete, state_reset, basket_add
from dragmetal.bot.states import ProductData
from datetime import datetime


@dp.callback_query_handler(Button('sell'), state="*")
async def accept_sell_btn(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки Продать"""
    logger.info("Пользователь {} нажал на кнопку Продать".format(call.from_user.id))
    data = await state.get_data()
    await state.update_data(type='sell')
    if users_stock_chak(data.get('user_profile')):
        btn = btn_users_metal(data.get('user_profile'), 'sell')
        await ProductData.type.set()
        return await call.message.edit_text("Что мы хотим продать?", parse_mode='html', reply_markup=btn)
    await call.message.edit_text("Ваш склад пуст. Просьба пополнить для начала склад.", parse_mode='html',
                                 reply_markup=btn_stock)


@dp.callback_query_handler(Button('sell-', True), state=ProductData.type)
async def accept_sell_metal(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки выбранного для продажи металла"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    metal_name = await convert_slug_to_name(call.data)
    data = await state.get_data()
    btn = btn_users_sample(data.get('user_profile'), call.data, 'sell')
    await state.update_data(metal_name=metal_name)
    await call.message.edit_text("Какой пробы?", parse_mode='html', reply_markup=btn)
    await ProductData.sample.set()


@dp.callback_query_handler(Button('add_to_basket'), state=ProductData.weight)
async def add_to_basket(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки Добавить в корзину"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    data = await state.get_data()
    user: UserBot = data.get('user_profile')
    if basket := user.users_basket.filter(status="active").first():
        await basket_add(basket, data)
        await state.update_data(basket=basket)
    else:
        basket = await new_basket_create(user, data)
        await state.update_data(basket=basket)
    title = "<b>****КОРЗИНА****</b>\n"
    text = await get_info(text=title, model=basket)
    await call.message.edit_text(text, reply_markup=btn_basket_continue, parse_mode='html')


@dp.callback_query_handler(Button('continue'), state=ProductData.weight)
async def sell_continue(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки Продолжить"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    await call.message.edit_reply_markup()
    data = await state.get_data()
    btn = btn_users_metal(data.get('user_profile'), 'sell')
    await ProductData.type.set()
    await bot.send_message(call.from_user.id, text="Что мы хотим продать еще?", parse_mode='html', reply_markup=btn)


@dp.callback_query_handler(Button('ordering'), state=ProductData.weight)
async def accept_ordering(call: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки Заказа"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    data = await state.get_data()
    user: UserBot = data.get('user_profile')
    if not user.users_basket.filter(status="active"):
        basket = await new_basket_create(user, data)
        await state.update_data(basket=basket)
    text = "Укажите пожалуйста адрес места скупки.\n\nПросьба ввести данные в формате:\n<i>Город, адрес</i>"
    await call.message.edit_text(text, parse_mode='html', reply_markup=btn_menu_back)
    await ProductData.address.set()


@dp.message_handler(state=ProductData.address)
async def accept_ordering(message: types.Message, state: FSMContext):
    """Обработка адрес места скупки"""
    logger.info("Пользователь {} ввел свой адрес".format(message.from_user.id))
    text = "Укажите пожалуйста дату и время скупки.\n\nПросьба ввести данные в формате:\n<i>ДД.ММ.ГГГГ чч:мм</i>"
    try:
        address_list = message.text.split(',')
        await state.update_data(city=address_list[0])
        await state.update_data(address=address_list[1].strip())
        await message.answer(text, parse_mode='html', reply_markup=btn_menu_back)
        await ProductData.date_time.set()
    except (ValueError, NameError, TypeError, IndexError):
        await message.answer(text="Введите пожалуйста адрес строго по шаблону:\n<i>Город, адрес</i>",
                             reply_markup=btn_menu_back, parse_mode='html')


@dp.message_handler(state=ProductData.date_time)
async def add_date_time(message: types.Message, state: FSMContext):
    """Обработка времени скупки и вывод результата"""
    logger.info("Пользователь {} ввел дату и время скупки".format(message.from_user.id))
    try:
        l_dt = message.text.split()
        l_d = l_dt[0].split('.')
        l_t = l_dt[1].split(':')
        dt = datetime(int(l_d[2]), int(l_d[1]), int(l_d[0]), int(l_t[0]), int(l_t[1]))
        await state.update_data(date_time=dt)
        data = await state.get_data()
        title = "<b>****ЗАКАЗ****</b>\n"
        text = await get_info(text=title, model=data.get('basket'))
        text += f"\n<b>Дата и время скупки:</b> <i>{message.text}</i>"
        await message.answer(text, reply_markup=btn_order_complete, parse_mode='html')
    except (ValueError, NameError, TypeError, IndexError):
        await message.answer(text="Введите пожалуйста дату и время строго по шаблону:\n<i>ДД.ММ.ГГГГ чч:мм</i>",
                             reply_markup=btn_menu_back, parse_mode='html')


@dp.callback_query_handler(Button('send'), state=ProductData.date_time)
async def complete_ordering(call: types.CallbackQuery, state: FSMContext):
    """Завершить Заказ"""
    logger.info("Пользователь {} нажал на кнопку {}".format(call.from_user.id, call.data))
    data = await state.get_data()
    await order_complete(data)
    await call.message.edit_text("Операция выполнена успешно.", reply_markup=btn_menu_back, parse_mode='html')
    await state_reset(state)
    print(data)
