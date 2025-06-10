import sys

from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, request
from rest_framework.parsers import *
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    UserSerializer, NewUserSerializer, InstrumentSerializer,
    L2OrderBookSerializer, LimitOrderSerializer, MarketOrderSerializer,
    LimitOrderBodySerializer, MarketOrderBodySerializer,
    CreateOrderResponseSerializer, OkSerializer, TransactionSerializer,
    DepositSerializer, WithdrawSerializer
)
import uuid
from datetime import datetime, timezone
from collections import defaultdict

def utcnow():
    """Return current UTC time as an ISO string with timezone."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
ORDERS = {}
ORDER_BOOK = defaultdict(lambda: {"BUY": [], "SELL": []})
TRADES = []
BALANCES = defaultdict(lambda: defaultdict(float))


def _remaining(order):
    return order["body"]["qty"] - order["filled"]


def _match_market(order):
    ticker = order["body"]["ticker"]
    direction = order["body"]["direction"]
    qty = _remaining(order)
    book = ORDER_BOOK[ticker]
    if direction == "BUY":
        orders = book["SELL"]
        orders.sort(key=lambda o: o["body"]["price"])
    else:
        orders = book["BUY"]
        orders.sort(key=lambda o: o["body"]["price"], reverse=True)
    i = 0
    while qty > 0 and i < len(orders):
        counter = orders[i]
        available = _remaining(counter)
        trade_qty = min(qty, available)
        if trade_qty <= 0:
            i += 1
            continue
        qty -= trade_qty
        order["filled"] += trade_qty
        counter["filled"] += trade_qty
        TRADES.append({
            "id": str(uuid.uuid4()),
            "timestamp": utcnow(),
            "ticker": ticker,
            "qty": trade_qty,
            "price": counter["body"].get("price", 0),
            "direction": direction,
            "order_id": order["id"],
            "user_id": order["user_id"],
        })
        if _remaining(counter) == 0:
            counter["status"] = "EXECUTED"
            orders.pop(i)
        else:
            counter["status"] = "PARTIALLY_EXECUTED"
            i += 1
    if _remaining(order) == 0:
        order["status"] = "EXECUTED"
    elif order["filled"] > 0:
        order["status"] = "PARTIALLY_EXECUTED"


def _match_limit(order):
    ticker = order["body"]["ticker"]
    direction = order["body"]["direction"]
    price = order["body"]["price"]
    qty = _remaining(order)
    book = ORDER_BOOK[ticker]
    if direction == "BUY":
        orders = book["SELL"]
        orders.sort(key=lambda o: o["body"]["price"])
        i = 0
        while qty > 0 and i < len(orders):
            counter = orders[i]
            if counter["body"]["price"] > price:
                break
            available = _remaining(counter)
            trade_qty = min(qty, available)
            if trade_qty <= 0:
                i += 1
                continue
            qty -= trade_qty
            order["filled"] += trade_qty
            counter["filled"] += trade_qty
            TRADES.append({
                "id": str(uuid.uuid4()),
                "timestamp": utcnow(),
                "ticker": ticker,
                "qty": trade_qty,
                "price": counter["body"].get("price", 0),
                "direction": direction,
                "order_id": order["id"],
                "user_id": order["user_id"],
            })
            if _remaining(counter) == 0:
                counter["status"] = "EXECUTED"
                orders.pop(i)
            else:
                counter["status"] = "PARTIALLY_EXECUTED"
                i += 1
        if _remaining(order) > 0:
            if order["filled"] > 0:
                order["status"] = "PARTIALLY_EXECUTED"
            book["BUY"].append(order)
            book["BUY"].sort(key=lambda o: o["body"]["price"], reverse=True)
        else:
            order["status"] = "EXECUTED"
    else:
        orders = book["BUY"]
        orders.sort(key=lambda o: o["body"]["price"], reverse=True)
        i = 0
        while qty > 0 and i < len(orders):
            counter = orders[i]
            if counter["body"]["price"] < price:
                break
            available = _remaining(counter)
            trade_qty = min(qty, available)
            if trade_qty <= 0:
                i += 1
                continue
            qty -= trade_qty
            order["filled"] += trade_qty
            counter["filled"] += trade_qty
            TRADES.append({
                "id": str(uuid.uuid4()),
                "timestamp": utcnow(),
                "ticker": ticker,
                "qty": trade_qty,
                "price": counter["body"].get("price", 0),
                "direction": direction,
                "order_id": order["id"],
                "user_id": order["user_id"],
            })
            if _remaining(counter) == 0:
                counter["status"] = "EXECUTED"
                orders.pop(i)
            else:
                counter["status"] = "PARTIALLY_EXECUTED"
                i += 1
        if _remaining(order) > 0:
            if order["filled"] > 0:
                order["status"] = "PARTIALLY_EXECUTED"
            book["SELL"].append(order)
            book["SELL"].sort(key=lambda o: o["body"]["price"])
        else:
            order["status"] = "EXECUTED"


def process_order(order):
    if "price" in order["body"]:
        _match_limit(order)
    else:
        _match_market(order)


def http_validation_error(msg, loc=None):
    if loc is None:
        loc = ["body"]
    return Response(
        {"detail": [{"loc": loc, "msg": msg, "type": "validation_error"}]},
        status=422
    )

User = get_user_model()

class RegisterView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(request_body=NewUserSerializer, responses={200: UserSerializer})
    def post(self, request):
        serializer = NewUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=422)
        username = serializer.validated_data['name']
        role = serializer.validated_data.get('role', User.Roles.USER)
        is_staff = role == User.Roles.ADMIN
        user = User.objects.create_user(username=username, role=role, is_staff=is_staff)
        data = {
            "id": str(user.id),
            "name": user.username,
            "role": user.role,
            "api_key": user.api_key,
        }
        return Response(data, status=200)

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
        book = ORDER_BOOK[ticker]
        bids = sorted(book["BUY"], key=lambda o: o["body"]["price"], reverse=True)[:limit]
        asks = sorted(book["SELL"], key=lambda o: o["body"]["price"])[:limit]
        orderbook = {
            "bid_levels": [{"price": o["body"]["price"], "qty": _remaining(o)} for o in bids],
            "ask_levels": [{"price": o["body"]["price"], "qty": _remaining(o)} for o in asks]
        }
        serializer = L2OrderBookSerializer(orderbook)
        return Response(serializer.data, status=200)

class TransactionHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, ticker):
        limit = request.GET.get("limit", 10)
        try:
            limit = int(limit)
            if not (1 <= limit <= 100):
                raise ValueError()
        except Exception:
            return http_validation_error("Invalid 'limit' parameter", ["query", "limit"])
        txs = [t for t in TRADES if t["ticker"] == ticker][:limit]
        serializer = TransactionSerializer(txs, many=True)
        return Response(serializer.data, status=200)

class BalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user_id = str(request.user.id)
        data = dict(BALANCES[user_id])
        return Response(data, status=200)

class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    # Accept JSON, form-urlencoded and multipart form data
    parser_classes = [JSONParser, FormParser, MultiPartParser]


    def get(self, request):
        user_id = str(request.user.id)
        orders = [o for o in ORDERS.values() if o["user_id"] == user_id]
        serializer = LimitOrderSerializer(orders, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(request_body=LimitOrderBodySerializer, responses={200: CreateOrderResponseSerializer})
    def post(self, request):
        body = request.data
        if "price" in body:
            serializer = LimitOrderBodySerializer(data=body)
        else:
            serializer = MarketOrderBodySerializer(data=body)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "status": "NEW",
            "user_id": str(request.user.id),
            "timestamp": utcnow(),
            "body": dict(serializer.validated_data),
            "filled": 0.0,
        }
        ORDERS[order_id] = order
        process_order(order)
        response = {"success": True, "order_id": order_id}
        return Response(response, status=200)

class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, order_id):
        order = ORDERS.get(str(order_id))
        if not order:
            return Response(status=404)
        serializer = LimitOrderSerializer(order)
        return Response(serializer.data, status=200)

    def delete(self, request, order_id):
        order = ORDERS.get(str(order_id))
        if not order:
            return Response(status=404)
        order["status"] = "CANCELLED"
        ticker = order["body"]["ticker"]
        direction = order["body"]["direction"]
        book = ORDER_BOOK[ticker][direction]
        if order in book:
            book.remove(order)
        ok = {"success": True}
        return Response(ok, status=200)

class AdminUserDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]
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
    permission_classes = [permissions.IsAdminUser]
    # Support JSON, form and multipart data
    parser_classes = [JSONParser, FormParser, MultiPartParser]


    @swagger_auto_schema(request_body=InstrumentSerializer, responses={200: OkSerializer})
    def post(self, request):
        print(
            f"\n>>> REQUEST LOG: {request.method} {request.get_full_path()}\n"
            f"Headers: {dict(request.headers)}\n")
        user_id = InstrumentSerializer.validated_data["user_id"]
        ticker = InstrumentSerializer.validated_data["ticker"]
        amount = InstrumentSerializer.validated_data["amount"]
        BALANCES[user_id][ticker] += amount
        user_id = InstrumentSerializer.validated_data["user_id"]
        ticker = InstrumentSerializer.validated_data["ticker"]
        amount = InstrumentSerializer.validated_data["amount"]
        balance = BALANCES[user_id][ticker]
        if balance < amount:
            return http_validation_error("Insufficient balance", ["body", "amount"])
        BALANCES[user_id][ticker] -= amount(
            f"Content-Type: {request.content_type}\n"
            f"Body: {request.body.decode(errors='replace')}\n",
            file=sys.stderr
        )
        serializer = InstrumentSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        ok = {"success": True}
        return Response(ok, status=200)

class AdminInstrumentDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]
    def delete(self, request, ticker):
        ok = {"success": True}
        return Response(ok, status=200)

class AdminBalanceDepositView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser, FormParser, MultiPartParser]


    @swagger_auto_schema(request_body=DepositSerializer, responses={200: OkSerializer})
    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        user_id = serializer.validated_data["user_id"]
        ticker = serializer.validated_data["ticker"]
        amount = serializer.validated_data["amount"]
        BALANCES[user_id][ticker] += amount
        ok = {"success": True}
        return Response(ok, status=200)

class AdminBalanceWithdrawView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser, FormParser, MultiPartParser]


    @swagger_auto_schema(request_body=WithdrawSerializer, responses={200: OkSerializer})
    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        user_id = serializer.validated_data["user_id"]
        ticker = serializer.validated_data["ticker"]
        amount = serializer.validated_data["amount"]
        balance = BALANCES[user_id][ticker]
        if balance < amount:
            return http_validation_error("Insufficient balance", ["body", "amount"])
        BALANCES[user_id][ticker] -= amount
        ok = {"success": True}
        return Response(ok, status=200)
