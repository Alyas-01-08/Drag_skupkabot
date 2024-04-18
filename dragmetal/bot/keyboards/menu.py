from aiogram.utils.callback_data import CallbackData
from django.conf import settings
from slugify import slugify
from dragmetal.bot.keyboards.list_btn import ListOfButtons
from dragmetal.models import PreciousMetal, UserBot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

btn_create_user = ListOfButtons(text=['Регистрация пользователя ⏩'], callback=['register']).inline_keyboard
btn_privacy_user = ListOfButtons(text=['Принять'], callback=['privacy']).inline_keyboard
btn_menu = ListOfButtons(text=['Склад', 'Калькулятор', 'Продать'], callback=['stock', 'calculator', 'sell'],
                         align=[2, 1]).inline_keyboard
btn_add_menu = ListOfButtons(text=['Добавить', 'Назад ⏪'], callback=['add', 'menu']).inline_keyboard
btn_confirm = ListOfButtons(text=['Подтвердить', 'Назад ⏪'], callback=['confirm', 'menu'], align=[2]).inline_keyboard
btn_ordering = ListOfButtons(text=['Оформить заказ', 'Добавить в корзину', 'Назад ⏪'],
                             callback=['ordering', 'add_to_basket', 'menu'], align=[2, 1]).inline_keyboard
btn_add_rm_menu = ListOfButtons(text=['Добавить', 'Удалить', 'Назад ⏪'],
                                callback=['add', 'remove', 'menu'], align=[2, 1]).inline_keyboard
btn_menu_back = ListOfButtons(text=['Назад ⏪'], callback=['menu']).inline_keyboard
# btn_reject_menu_back = ListOfButtons(text=['Отменить все и Назад ⏪'], callback=['menu']).inline_keyboard
btn_stock = ListOfButtons(text=['Склад', 'Назад ⏪'], callback=['stock', 'menu'], align=[2]).inline_keyboard
btn_order_complete = ListOfButtons(text=['Отправить', 'Назад ⏪'], callback=['send', 'menu'], align=[2]).inline_keyboard
btn_basket_continue = ListOfButtons(text=['Продолжить', 'Оформить заказ', 'Назад ⏪'],
                                    callback=['continue', 'ordering', 'menu'], align=[2, 1]).inline_keyboard
btn_geo = KeyboardButton(text='GIS', request_location=True)
geo_markup = ReplyKeyboardMarkup(resize_keyboard=True).add(btn_geo)


def btn_metal_menu(command: str = ''):
    """Генерирует inline клавиатуру содержащий названия металлов"""
    texts = [i.name for i in PreciousMetal.objects.all()]
    callbacks = [slugify(f"{command} {i.name}") for i in PreciousMetal.objects.all()]
    texts.append('Назад ⏪')
    callbacks.append('menu')
    return ListOfButtons(text=texts, callback=callbacks).inline_keyboard


def btn_users_metal(user: UserBot, command: str):
    """Генерирует inline клавиатуру содержащий названия только металлов,
    которые имеются на складе конкретного пользователя"""
    precious = set(i.sample.precious for i in user.users_stock.all())
    texts = [i.name for i in precious]
    callbacks = [slugify(f"{command} {i.name}") for i in precious]
    texts.append('Назад ⏪')
    callbacks.append('menu')
    return ListOfButtons(text=texts, callback=callbacks).inline_keyboard


def btn_samples(call_data: str, command: str):
    """Генерирует inline клавиатуру содержащий все возможные пробы определенного металла"""
    ending = call_data.split('-')[-1]
    for metal in PreciousMetal.objects.all():
        if slugify(metal.name) == ending:
            texts = [i.sample for i in metal.sample.all()]
            callbacks = [slugify(f"{i.sample} {command}") for i in metal.sample.all()]
            texts.append('Назад ⏪')
            callbacks.append('menu')
            return ListOfButtons(text=texts, callback=callbacks).inline_keyboard


def btn_users_sample(user: UserBot, call_data: str, command: str):
    """Генерирует inline клавиатуру содержащий пробы определенного металла у определенного пользователя"""
    samples = [i.sample for i in user.users_stock.all() if slugify(i.sample.precious.name) in call_data]
    texts = [i.sample for i in samples]
    callbacks = [slugify(f"{i.sample} {command}") for i in samples]
    texts.append('Назад ⏪')
    callbacks.append('menu')
    return ListOfButtons(text=texts, callback=callbacks).inline_keyboard


about_callback = CallbackData('about_project', 'section')
btn_url = ListOfButtons(text=['Instagram', 'Канал SmartGift'],
                        callback=['url:https://instagram.com/smartgift.official?igshid=YmMyMTA2M2Y=',
                                  'url:https://t.me/SmartGift_company']).inline_keyboard

btn_user_type = ListOfButtons(text=['Юр. лицо', 'Физ. лицо'], callback=['entity', 'physical']).inline_keyboard

btn_wallet = ListOfButtons(text=['Меню 🌐', 'ВВОД 🏦', 'ВЫВОД 💰'],
                           callback=['menu', 'ENTER', 'CONCLUSION'], align=[1, 2]).inline_keyboard
btn_presentation = ListOfButtons(text=['Меню 🌐', 'Посмотреть'],
                                 callback=['menu', 'url:https://yandex.ru/']).inline_keyboard


def btn_program(url_ref): return ListOfButtons(
    text=['Меню 🌐', 'Пригласить друга', 'Моя команда 👥'],
    callback=['menu', 'invite', f'url:{settings.HOST_NAME}tree/{url_ref}'], align=[2, 1]).inline_keyboard


btn_success = ListOfButtons(text=['Меню 🌐', 'Продолжить ⏩'], callback=['menu', 'true']).inline_keyboard
btn_creat_wallet = ListOfButtons(text=['Меню 🌐', 'Создать ✅'], callback=['menu', 'true']).inline_keyboard
btn_enter_wallet = ListOfButtons(text=['Готово ✅', 'Удалить ❌'],
                                 callback=['menu', 'wallet|delete']).inline_keyboard
# wallet|ready готов к выводу
btn_del_wallet = ListOfButtons(text=['Подтвердить', 'Отмена'],
                               callback=['del|ready', 'del|cancellation']).inline_keyboard


def btn_back(call): return ListOfButtons(text=['Назад⏪'], callback=[call]).inline_keyboard


def btn_table(data):
    text = []
    callback = []
    for i in data:
        text.append(i.name)
        callback.append(f'GiftType_{i.id}')
    return ListOfButtons(text=text + ['Назад⏪'], callback=callback + ['Выбрать стол']).inline_keyboard


def about_markup(checked=''):
    texts = ['Столы и Роли', 'Даритель', 'Партнер', 'Ментор', 'Мастер']
    btn_about = ListOfButtons(text=[i if i != checked else i + '👁️' for i in texts],
                              callback=[about_callback.new('Столы и Роли'),
                                        about_callback.new('Даритель'),
                                        about_callback.new('Партнер'),
                                        about_callback.new('Ментор'),
                                        about_callback.new('Мастер')], align=[1, 2, 2]).inline_keyboard
    return btn_about
