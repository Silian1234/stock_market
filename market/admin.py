from django.contrib import admin
from .models import User, Account, Stock, Order, Trade


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'is_active', 'is_staff', 'api_key')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance')
    search_fields = ('user__username',)


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'name', 'current_price')
    search_fields = ('symbol', 'name')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'stock', 'order_type', 'order_mode',
        'price', 'quantity', 'remaining_quantity', 'created_at'
    )
    search_fields = ('user__username', 'stock__symbol')
    list_filter = ('order_type', 'order_mode')


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'stock', 'buyer', 'seller', 'price', 'quantity', 'created_at')
    search_fields = ('stock__symbol', 'buyer__username', 'seller__username')
    list_filter = ('stock__symbol',)