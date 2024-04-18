from __future__ import annotations

import uuid
from typing import Union, Optional, Tuple

from aiogram.types import User
from asgiref.sync import sync_to_async

from django.db import models
from django.db.models import QuerySet, Manager

from loguru import logger

from utils.models import CreateUpdateTracker, nb, GetOrNoneManager, CreateTracker


class UUIDMixin(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField('ID', primary_key=True, default=uuid.uuid4, editable=False)


class AdminUserManager(Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class UserBot(CreateUpdateTracker):
    id = models.PositiveBigIntegerField(primary_key=True)  # telegram_id
    username = models.CharField(max_length=32, **nb)
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256, **nb)
    language_code = models.CharField(max_length=8, help_text="Telegram client's lang", **nb)
    deep_link = models.CharField(max_length=64, **nb)
    is_blocked_bot = models.BooleanField(default=False)
    is_bot = models.BooleanField(default=False)
    chat_id_partner = models.CharField(max_length=200, **nb)
    is_admin = models.BooleanField(default=False)
    user_data = models.JSONField('Пользовательские данные', **nb)
    privacy = models.BooleanField('Соглашение', default=False)

    objects = GetOrNoneManager()  # user = User.objects.get_or_none(user_id=<some_id>)
    admins = AdminUserManager()  # User.admins.all()

    def __str__(self):
        return f'@{self.username}' if self.username is not None else f'{self.id}'

    @classmethod
    def get_user_and_created(cls, user_data: User) -> Tuple[UserBot, bool]:
        """ python-telegram-bot's Update, Context --> User instance """
        data = user_data.to_python()
        data.pop('id', None)
        data.pop('is_premium', None)
        u, created = cls.objects.update_or_create(id=user_data.id, defaults=data)
        logger.info(f"User {u.tg_str} created: {created}")

        return u, created

    @classmethod
    async def as_get_user(cls, user_data: User) -> UserBot:
        u, _ = await sync_to_async(cls.get_user_and_created)(user_data)
        return u

    async def as_save(self):
        await sync_to_async(self.save)()

    @classmethod
    def get_user(cls, user_data: User) -> UserBot:
        u, _ = cls.get_user_and_created(user_data)
        return u

    @classmethod
    def get_user_by_username_or_user_id(cls, username_or_user_id: Union[str, int]) -> Optional[UserBot]:
        """ Search user in DB, return User or None if not found """
        username = str(username_or_user_id).replace("@", "").strip().lower()
        if username.isdigit():  # user_id
            return cls.objects.filter(id=int(username)).first()
        return cls.objects.filter(username__iexact=username).first()

    @property
    def invited_users(self) -> QuerySet[UserBot]:
        return UserBot.objects.filter(deep_link=str(self.id), created_at__gt=self.created_at)

    @property
    def tg_str(self) -> str:
        if self.username:
            return f'@{self.username}'
        return f"{self.first_name} {self.last_name or ''}"

    @property
    def info_dict(self) -> dict:
        """Возвращает словарь хранящий информацию о драгметаллах пользователя на складе"""
        data = {}
        for stock in self.users_stock.all():
            key = stock.sample.precious.name
            if k := data.get(key):
                k.append(f"\t*{stock.sample.sample} - {stock.weight}г.\n\t  Стоимость: {stock.total_amount}₽\n")
            else:
                data[key] = [f"\t*{stock.sample.sample} - {stock.weight}г.\n\t  Стоимость: "
                             f"{stock.total_amount}₽\n"]
        return data

    @property
    def total_amount(self):
        """Общая сумма в ₽"""
        return sum(i.total_amount for i in self.users_stock.all())

    class Meta:
        ordering = ['is_admin', ]
        verbose_name = 'Пользователь Бота'
        verbose_name_plural = 'Пользователи Бота'


class PreciousMetal(UUIDMixin, CreateUpdateTracker):
    name = models.CharField('Название', max_length=20)
    objects = GetOrNoneManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Драгметалл'
        verbose_name_plural = 'Драгметаллы'


class SampleMetal(UUIDMixin, CreateUpdateTracker):
    precious = models.ForeignKey(PreciousMetal, on_delete=models.CASCADE, related_name='sample')
    sample = models.PositiveIntegerField('Проба')
    price = models.DecimalField('Цена за грамм', default=0, max_digits=15, decimal_places=0)
    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.precious} - {self.sample}'

    class Meta:
        verbose_name = 'Проба'
        verbose_name_plural = 'Пробы'


class Stock(UUIDMixin, CreateUpdateTracker):
    user = models.ForeignKey(UserBot, on_delete=models.CASCADE, related_name='users_stock')
    sample = models.ForeignKey(SampleMetal, on_delete=models.CASCADE)
    weight = models.DecimalField('Масса', default=0, max_digits=15, decimal_places=3)
    objects = GetOrNoneManager()

    def __str__(self):
        return str(self.sample.sample)

    @property
    def total_amount(self):
        """Сумма в ₽"""
        return self.sample.price * self.weight

    class Meta:
        verbose_name = 'Склад'
        verbose_name_plural = 'Склады'


class Basket(UUIDMixin, CreateUpdateTracker):
    user = models.ForeignKey(UserBot, on_delete=models.CASCADE, related_name='users_basket')
    status = models.CharField('Статус корзины', max_length=10, default='new',
                              choices=(('new', 'Новый'), ('active', 'Активен'), ('not_active', 'не активен')))

    def __str__(self):
        return f'{self.user}.basket: {self.status}'

    @property
    def info_dict(self) -> dict:
        """Возвращает словарь хранящий информацию о драгметаллах в корзине"""
        data = {}
        for choice in self.basket_choice.all():
            key = choice.stock.sample.precious.name
            if k := data.get(key):
                k.append(f"\t*{choice.stock.sample.sample} - {choice.weight}г.\n\t  Стоимость: {choice.amount}₽\n")
            else:
                data[key] = [f"\t*{choice.stock.sample.sample} - {choice.weight}г.\n\t  Стоимость: "
                             f"{choice.amount}₽\n"]
        return data

    @property
    def total_amount(self):
        """Общая сумма в ₽"""
        return sum(i.amount for i in self.basket_choice.all())

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'


class BasketChoice(UUIDMixin, CreateUpdateTracker):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE, related_name='basket_choice')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='stock_choice')
    weight = models.DecimalField('Масса', default=0, max_digits=15, decimal_places=3)
    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.stock} {self.basket.status}'

    @property
    def amount(self):
        """Сумма в ₽"""
        return self.stock.sample.price * self.weight

    class Meta:
        verbose_name = 'Выбор в корзину'
        verbose_name_plural = 'Выборы в корзину'


class Order(UUIDMixin, CreateUpdateTracker):
    user = models.ForeignKey(UserBot, on_delete=models.CASCADE, related_name='order_users_stock')
    status = models.CharField('Статус Заказа', max_length=10, default='new',
                              choices=(('new', 'Новый'), ('rejected', 'Отменена'), ('waiting', 'В ожидании'),
                                       ('completed', 'Завершена')))
    total_amount = models.DecimalField('Общая сумма заказа', default=0, max_digits=15, decimal_places=0)
    sale_time = models.DateTimeField('Время продажи')
    data = models.JSONField(**nb)
    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.user}.order ({self.status})'

    class Meta:
        ordering = ['created_at', ]
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'


class OrderChoice(UUIDMixin, CreateUpdateTracker):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_choice')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='order_stock_choice')
    weight = models.DecimalField('Масса', default=0, max_digits=15, decimal_places=3)
    objects = GetOrNoneManager()

    def __str__(self):
        return f'{self.stock} ({self.order.status})'

    @property
    def amount(self):
        """Сумма в ₽"""
        return self.stock.sample.price * self.weight

    class Meta:
        ordering = ['created_at', ]
        verbose_name = 'Товар выделенный в заказ'
        verbose_name_plural = 'Товары выделенные в заказ'
