from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    pass

class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts')
    currency = models.CharField(max_length=10, default="USD")
    balance = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username}'s account ({self.currency})"

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    initial_price = models.FloatField()
    available_quantity = models.IntegerField()

    def __str__(self):
        return self.symbol

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('MARKET', 'Market'),
        ('LIMIT', 'Limit'),
    ]
    SIDE_CHOICES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=10, choices=ORDER_TYPE_CHOICES)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    price = models.FloatField(null=True, blank=True)
    quantity = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}: {self.side} {self.quantity} of {self.stock.symbol}"
