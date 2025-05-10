from django.contrib import admin
from .models import User, Account, Stock, Holding, Order, Trade

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email')
    search_fields = ('username', 'email')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'balance')
    search_fields = ('user__username',)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('id', 'symbol', 'name', 'current_price')
    search_fields = ('symbol', 'name')

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stock', 'quantity')
    search_fields = ('user__username', 'stock__symbol')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'stock', 'order_type', 'order_mode', 'quantity', 'remaining_quantity', 'price', 'is_filled')
    list_filter = ('order_type', 'order_mode', 'is_filled')
    search_fields = ('user__username', 'stock__symbol')

@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'stock', 'buyer', 'seller', 'price', 'quantity', 'created_at')
    search_fields = ('stock__symbol', 'buyer__username', 'seller__username')