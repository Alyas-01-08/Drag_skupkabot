import json
from decimal import Decimal, InvalidOperation

from aiogram.dispatcher import FSMContext
from slugify import slugify

from dragmetal.bot.keyboards.menu import btn_menu
from dragmetal.bot.loader import bot
from dragmetal.models import UserBot, PreciousMetal, SampleMetal, Stock, Basket, BasketChoice, Order


async def create_user(data: dict, message_id):
    """Регистрирует пользователя"""
    u = data.pop('user_profile')
    u.user_data = json.dumps(data, ensure_ascii=False)
    u.privacy = True
    u.save()
    message = "Главное меню\! Вы можете пользоваться всеми возможностями бота"
    await bot.send_message(u.id, message, reply_markup=btn_menu)
    await bot.delete_message(u.id, message_id)


async def get_info(text: str, model):
    """Генерирует текс подробной информации о драгметаллах пользователя"""
    for k, v in model.info_dict.items():
        text += f"\n<b>{k}:</b>\n"
        for i in v:
            text += i
    text += f"\n<b>Общая стоимость:</b> {model.total_amount}₽"
    return text


async def convert_slug_to_name(call_data: str):
    """Возвращает название метала из slug"""
    for m in PreciousMetal.objects.all():
        if slugify(m.name) in call_data:
            return m.name


async def manage_stock(data: dict):
    """Добавление в Склад/Удаление из Склада"""
    user: UserBot = data.get('user_profile')
    instance: SampleMetal = data.get('sample_instance')
    weight = data.get('weight')
    if stock := user.users_stock.get_or_none(sample=instance):
        if data.get('type') == 'add':
            stock.weight += weight
            stock.save()
        else:
            stock.weight -= weight
            if stock.weight <= Decimal('0'):
                stock.delete()
            else:
                stock.save()
    else:
        Stock.objects.create(user=user, sample=instance, weight=weight)


async def new_basket_create(user: UserBot, data: dict):
    """Создает новую корзину"""
    basket = user.users_basket.create(status="active")
    stock = user.users_stock.get_or_none(sample=data.get('sample_instance'))
    basket.basket_choice.create(stock=stock, weight=data.get('weight'))
    return basket


async def basket_add(basket: Basket, data: dict):
    """Добавляет в корзину"""
    stock = basket.user.users_stock.get_or_none(sample=data.get('sample_instance'))
    choice, created = basket.basket_choice.get_or_create(stock=stock)
    choice.weight += data.get('weight')
    choice.save()
    return basket


async def order_complete(data: dict):
    """Оформляет заказ"""
    basket: Basket = data.get('basket')
    user = data.get('user_profile')
    dt = data.get('date_time')
    order = Order.objects.create(user=user, status='waiting', total_amount=basket.total_amount, sale_time=dt)
    for choice in basket.basket_choice.all():
        order.order_choice.create(stock=choice.stock, weight=choice.weight)
        choice.stock.weight -= choice.weight
        choice.stock.save()
    address_data = {
        'city': data.get('city'),
        'address': data.get('address')
    }
    order.data = json.dumps(address_data, ensure_ascii=False)
    order.save()


async def state_reset(state: FSMContext):
    """Сброс состояние оставляя user_profile"""
    data = await state.get_data()
    user = data.get('user_profile')
    await state.reset_state()
    await state.update_data(user_profile=user)


async def basket_reject(user: UserBot):
    """Деактивация корзин"""
    if baskets := user.users_basket.filter(status='active'):
        for basket in baskets:
            basket.status = 'not_active'
            basket.save()


def get_user_type(user: UserBot):
    """Проверка типа пользователя"""
    user_data = json.loads(user.user_data)
    if user_data.get('user_type') == 'Физ. лицо':
        return 'physical'
    return 'entity'


def get_sample_obj(metal_name: str, sample: str):
    """Возвращает экземпляр класса Sample следуя из названия металла и пробы"""
    metal: PreciousMetal = PreciousMetal.objects.get_or_none(name=metal_name)
    return metal.sample.get_or_none(sample=int(sample))


def weight_in_sell_chak(data: dict, weight: Decimal):
    sample: SampleMetal = data.get('sample_instance')
    user: UserBot = data.get('user_profile')
    stock = user.users_stock.get_or_none(sample=sample)
    if basket := user.users_basket.filter(status="active").first():
        if choice := basket.basket_choice.get_or_none(stock=stock):
            weight += choice.weight

    if stock.weight < weight:
        return True
    return False


def users_stock_chak(user: UserBot):
    return user.users_stock.all()
