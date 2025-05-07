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
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]
    ORDER_MODE_CHOICES = [
        ('market', 'Market'),
        ('limit', 'Limit'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPE_CHOICES)
    order_mode = models.CharField(max_length=6, choices=ORDER_MODE_CHOICES, default='market')
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_filled = models.BooleanField(default=False)
    remaining_quantity = models.PositiveIntegerField()

class Trade(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sales')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='purchases')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)