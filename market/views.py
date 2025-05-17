from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import (
    UserSerializer, NewUserSerializer, InstrumentSerializer,
    L2OrderBookSerializer, LimitOrderSerializer, MarketOrderSerializer,
    LimitOrderBodySerializer, MarketOrderBodySerializer,
    CreateOrderResponseSerializer, OkSerializer, TransactionSerializer
)
import uuid
from datetime import datetime

def http_validation_error(msg, loc=None):
    if loc is None:
        loc = ["body"]
    return Response(
        {"detail": [{"loc": loc, "msg": msg, "type": "validation_error"}]},
        status=422
    )

class RegisterView(APIView):
    def post(self, request):
        serializer = NewUserSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        user = {
            "id": str(uuid.uuid4()),
            "name": serializer.validated_data['name'],
            "role": "USER",
            "api_key": "key-" + str(uuid.uuid4())
        }
        return Response(user, status=200)

class InstrumentListView(APIView):
    def get(self, request):
        instruments = [
            {"name": "Memecoin", "ticker": "MEMCOIN"},
            {"name": "Dodge", "ticker": "DODGE"}
        ]
        serializer = InstrumentSerializer(instruments, many=True)
        return Response(serializer.data, status=200)

class L2OrderBookView(APIView):
    def get(self, request, ticker):
        limit = request.GET.get("limit", 10)
        try:
            limit = int(limit)
            if not (1 <= limit <= 25):
                raise ValueError()
        except Exception:
            return http_validation_error("Invalid 'limit' parameter", ["query", "limit"])
        orderbook = {
            "bid_levels": [],
            "ask_levels": []
        }
        serializer = L2OrderBookSerializer(orderbook)
        return Response(serializer.data, status=200)

class TransactionHistoryView(APIView):
    def get(self, request, ticker):
        limit = request.GET.get("limit", 10)
        try:
            limit = int(limit)
            if not (1 <= limit <= 100):
                raise ValueError()
        except Exception:
            return http_validation_error("Invalid 'limit' parameter", ["query", "limit"])
        serializer = TransactionSerializer([], many=True)
        return Response(serializer.data, status=200)

class BalanceView(APIView):
    def get(self, request):
        data = {"MEMCOIN": 0, "DODGE": 100500}
        return Response(data, status=200)

class OrderListCreateView(APIView):
    def get(self, request):
        orders = []
        return Response(orders, status=200)

    def post(self, request):
        body = request.data
        if "price" in body:
            serializer = LimitOrderBodySerializer(data=body)
        else:
            serializer = MarketOrderBodySerializer(data=body)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        response = {
            "success": True,
            "order_id": str(uuid.uuid4())
        }
        return Response(response, status=200)

class OrderDetailView(APIView):
    def get(self, request, order_id):
        order = {
            "id": str(order_id),
            "status": "NEW",
            "user_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "body": {
                "direction": "BUY",
                "ticker": "MEMCOIN",
                "qty": 1,
                "price": 100
            },
            "filled": 0
        }
        serializer = LimitOrderSerializer(order)
        return Response(serializer.data, status=200)

    def delete(self, request, order_id):
        ok = {"success": True}
        return Response(ok, status=200)

class AdminUserDeleteView(APIView):
    def delete(self, request, user_id):
        user = {
            "id": str(user_id),
            "name": "test",
            "role": "USER",
            "api_key": "key-" + str(uuid.uuid4())
        }
        serializer = UserSerializer(user)
        return Response(serializer.data, status=200)

class AdminInstrumentCreateView(APIView):
    def post(self, request):
        serializer = InstrumentSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        ok = {"success": True}
        return Response(ok, status=200)

class AdminInstrumentDeleteView(APIView):
    def delete(self, request, ticker):
        ok = {"success": True}
        return Response(ok, status=200)

class AdminBalanceDepositView(APIView):
    def post(self, request):
        body = request.data
        if "user_id" not in body or "ticker" not in body or "amount" not in body:
            return http_validation_error("user_id, ticker и amount обязательны")
        ok = {"success": True}
        return Response(ok, status=200)

class AdminBalanceWithdrawView(APIView):
    def post(self, request):
        body = request.data
        if "user_id" not in body or "ticker" not in body or "amount" not in body:
            return http_validation_error("user_id, ticker и amount обязательны")
        ok = {"success": True}
        return Response(ok, status=200)
