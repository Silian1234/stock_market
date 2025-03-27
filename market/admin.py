from django.contrib import admin
from .models import User, Account, Stock, Order

admin.site.register(User)
admin.site.register(Account)
admin.site.register(Stock)
admin.site.register(Order)
