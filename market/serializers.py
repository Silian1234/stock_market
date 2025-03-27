from rest_framework import serializers
from .models import Order, Stock, Account, User

class OrderCreateSerializer(serializers.Serializer):
    stock_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    side = serializers.ChoiceField(choices=[("BUY", "Buy"), ("SELL", "Sell")])
    order_type = serializers.ChoiceField(choices=[("MARKET", "Market"), ("LIMIT", "Limit")], default="MARKET")
    price = serializers.FloatField(required=False, allow_null=True)

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
