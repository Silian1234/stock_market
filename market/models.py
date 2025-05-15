from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        if not self.api_key:
            import secrets
            self.api_key = secrets.token_hex(20)
        super().save(*args, **kwargs)


class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=0)


class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=20, decimal_places=2)


class Order(models.Model):
    class OrderType(models.TextChoices):
        BUY = "buy", "Buy"
        SELL = "sell", "Sell"

    class OrderMode(models.TextChoices):
        LIMIT = "limit", "Limit"
        MARKET = "market", "Market"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    order_type = models.CharField(max_length=4, choices=OrderType.choices)
    order_mode = models.CharField(max_length=6, choices=OrderMode.choices)
    price = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    is_filled = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Trade(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buy_trades')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sell_trades')
    price = models.DecimalField(max_digits=20, decimal_places=2)
    quantity = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
