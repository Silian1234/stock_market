from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username}'s Account"


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=20, decimal_places=2)

    def __str__(self):
        return self.symbol


class Holding(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'stock')

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}: {self.quantity}"


class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('buy', 'Buy'),
        ('sell', 'Sell')
    ]

    ORDER_MODE_CHOICES = [
        ('limit', 'Limit'),
        ('market', 'Market')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPE_CHOICES)
    order_mode = models.CharField(max_length=6, choices=ORDER_MODE_CHOICES)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    remaining_quantity = models.PositiveIntegerField()
    is_filled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order_type.upper()} {self.quantity} {self.stock.symbol}"


class Trade(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchased_trades')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sold_trades')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} {self.stock.symbol} at {self.price}"
