# market/serializers.py

from rest_framework import serializers
import uuid

class UserSerializer(serializers.Serializer):
    id = serializers.UUIDField(format='hex_verbose')
    name = serializers.CharField()
    role = serializers.ChoiceField(choices=[('USER', 'USER'), ('ADMIN', 'ADMIN')])
    api_key = serializers.CharField()

class NewUserSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3)

class InstrumentSerializer(serializers.Serializer):
    name = serializers.CharField()
    ticker = serializers.RegexField(regex=r'^[A-Z]{2,10}$')

class LevelSerializer(serializers.Serializer):
    price = serializers.IntegerField()
    qty = serializers.IntegerField()

class L2OrderBookSerializer(serializers.Serializer):
    bid_levels = LevelSerializer(many=True)
    ask_levels = LevelSerializer(many=True)

class LimitOrderBodySerializer(serializers.Serializer):
    direction = serializers.ChoiceField(choices=[('BUY', 'BUY'), ('SELL', 'SELL')])
    ticker = serializers.CharField()
    qty = serializers.IntegerField(min_value=1)
    price = serializers.IntegerField(min_value=1)

class MarketOrderBodySerializer(serializers.Serializer):
    direction = serializers.ChoiceField(choices=[('BUY', 'BUY'), ('SELL', 'SELL')])
    ticker = serializers.CharField()
    qty = serializers.IntegerField(min_value=1)

class LimitOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField(format='hex_verbose')
    status = serializers.ChoiceField(choices=[('NEW','NEW'),('EXECUTED','EXECUTED'),('PARTIALLY_EXECUTED','PARTIALLY_EXECUTED'),('CANCELLED','CANCELLED')])
    user_id = serializers.UUIDField(format='hex_verbose')
    timestamp = serializers.DateTimeField()
    body = LimitOrderBodySerializer()
    filled = serializers.IntegerField(default=0)

class MarketOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField(format='hex_verbose')
    status = serializers.ChoiceField(choices=[('NEW','NEW'),('EXECUTED','EXECUTED'),('PARTIALLY_EXECUTED','PARTIALLY_EXECUTED'),('CANCELLED','CANCELLED')])
    user_id = serializers.UUIDField(format='hex_verbose')
    timestamp = serializers.DateTimeField()
    body = MarketOrderBodySerializer()

class CreateOrderResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    order_id = serializers.UUIDField(format='hex_verbose')

class OkSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)

class TransactionSerializer(serializers.Serializer):
    ticker = serializers.CharField()
    amount = serializers.IntegerField()
    price = serializers.IntegerField()
    timestamp = serializers.DateTimeField()

class ValidationErrorSerializer(serializers.Serializer):
    loc = serializers.ListField(child=serializers.CharField())
    msg = serializers.CharField()
    type = serializers.CharField()

class HTTPValidationErrorSerializer(serializers.Serializer):
    detail = ValidationErrorSerializer(many=True)
