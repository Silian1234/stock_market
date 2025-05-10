from rest_framework import serializers
from .models import User, Account, Stock, Holding, Order, Trade
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email']


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ['id', 'balance']


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ['id', 'symbol', 'name', 'current_price']


class HoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model = Holding
        fields = ['id', 'stock', 'quantity']


class OrderCreateSerializer(serializers.Serializer):
    stock_id = serializers.IntegerField()
    order_type = serializers.ChoiceField(choices=['buy', 'sell'])
    order_mode = serializers.ChoiceField(choices=['limit', 'market'])
    quantity = serializers.IntegerField(min_value=1)
    price = serializers.DecimalField(max_digits=20, decimal_places=2, required=False)

    def validate(self, data):
        if data['order_mode'] == 'limit' and data.get('price') is None:
            raise serializers.ValidationError("Price is required for limit orders.")
        if data['order_mode'] == 'market':
            data['price'] = None  # явно устанавливаем None
        return data


class OrderSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'stock', 'order_type', 'order_mode', 'price',
            'quantity', 'remaining_quantity', 'is_filled', 'created_at'
        ]


class TradeSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)

    class Meta:
        model = Trade
        fields = ['id', 'stock', 'buyer', 'seller', 'price', 'quantity', 'created_at']