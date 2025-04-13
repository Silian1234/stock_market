from rest_framework import serializers
from .models import User, Order, Stock, Account

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ("username", "email", "password", "first_name", "last_name")
    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

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
