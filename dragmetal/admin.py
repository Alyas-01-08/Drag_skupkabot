from django.contrib import admin
from django.db.models import QuerySet

from dragmetal.models import UserBot, PreciousMetal, SampleMetal, Stock, Basket, BasketChoice, Order, OrderChoice


class OrderChoiceInline(admin.TabularInline):
    model = OrderChoice
    extra = 1


class BasketChoiceInline(admin.TabularInline):
    model = BasketChoice
    extra = 1


class ParameterInline(admin.TabularInline):
    model = SampleMetal
    extra = 1


@admin.register(UserBot)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'username', 'first_name', 'last_name',
        'created_at', 'updated_at', "privacy",
    ]
    list_filter = ["is_blocked_bot", ]
    search_fields = ('username', 'id')


@admin.register(PreciousMetal)
class PreciousMetalAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    list_display_links = ("id",)
    inlines = [ParameterInline]


@admin.register(SampleMetal)
class SampleMetalAdmin(admin.ModelAdmin):
    list_display = ['id', 'precious', 'sample', 'price']
    list_display_links = ("id",)
    list_filter = ["precious", "sample"]
    search_fields = ('precious', 'id', 'sample')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'sample', 'weight']
    list_display_links = ("id",)
    list_filter = ["user", "sample"]
    search_fields = ('user', 'id', 'sample')


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status']
    list_display_links = ("id",)
    inlines = [BasketChoiceInline]
    list_filter = ["user", "status"]
    search_fields = ('user', 'id')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'sale_time']
    list_display_links = ("id",)
    inlines = [OrderChoiceInline]
    list_filter = ["user", "status"]
    search_fields = ('user', 'id')
    actions = ['order_complete', 'order_reject']

    @admin.action(description="Завершить заказ")
    def order_complete(self, request, qs: QuerySet):
        qs.update(status='completed')

    @admin.action(description="Отменить заказ")
    def order_reject(self, request, qs: QuerySet):
        qs.update(status='rejected')


@admin.register(BasketChoice)
class BasketChoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'basket',  'weight']
    list_display_links = ("id",)


@admin.register(OrderChoice)
class OrderChoiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'stock', 'weight']
    list_display_links = ("id",)
