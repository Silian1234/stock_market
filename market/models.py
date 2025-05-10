from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    # можно расширить позже, если нужно
    pass


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)  # USD

    def __str__(self):
        return f"{self.user.username} (Balance: {self.balance} USD)"


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return f"{self.symbol}"


class Holding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}: {self.quantity} shares"


class Order(models.Model):
    ORDER_TYPES = (
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    )
    ORDER_MODES = (
        ('limit', 'Limit'),
        ('market', 'Market'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPES)
    order_mode = models.CharField(max_length=6, choices=ORDER_MODES)
    price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    is_filled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class Trade(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades_as_buyer')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades_as_seller')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
