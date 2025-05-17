from rest_framework import serializers

class NewUserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)

class UserSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    role = serializers.CharField()
    api_key = serializers.CharField()

class InstrumentSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    ticker = serializers.CharField(max_length=20)

class L2LevelSerializer(serializers.Serializer):
    price = serializers.FloatField()
    qty = serializers.FloatField()

class L2OrderBookSerializer(serializers.Serializer):
    bid_levels = L2LevelSerializer(many=True)
    ask_levels = L2LevelSerializer(many=True)

class TransactionSerializer(serializers.Serializer):
    id = serializers.CharField()
    timestamp = serializers.DateTimeField()
    ticker = serializers.CharField()
    qty = serializers.FloatField()
    price = serializers.FloatField()
    direction = serializers.ChoiceField(choices=["BUY", "SELL"])
    order_id = serializers.CharField()
    user_id = serializers.CharField()

class LimitOrderBodySerializer(serializers.Serializer):
    direction = serializers.ChoiceField(choices=["BUY", "SELL"])
    ticker = serializers.CharField()
    qty = serializers.FloatField()
    price = serializers.FloatField()

class MarketOrderBodySerializer(serializers.Serializer):
    direction = serializers.ChoiceField(choices=["BUY", "SELL"])
    ticker = serializers.CharField()
    qty = serializers.FloatField()

class CreateOrderResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    order_id = serializers.CharField()

class LimitOrderSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    user_id = serializers.CharField()
    timestamp = serializers.CharField()
    body = LimitOrderBodySerializer()
    filled = serializers.FloatField()

class MarketOrderSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.CharField()
    user_id = serializers.CharField()
    timestamp = serializers.CharField()
    body = MarketOrderBodySerializer()
    filled = serializers.FloatField()

class OkSerializer(serializers.Serializer):
    success = serializers.BooleanField()

class DepositSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    ticker = serializers.CharField()
    amount = serializers.FloatField()

class WithdrawSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    ticker = serializers.CharField()
    amount = serializers.FloatField()
