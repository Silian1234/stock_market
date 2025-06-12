# market/views.py
import sys
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from .models import Account
from .serializers import (
    CreateOrderResponseSerializer,
    DepositSerializer,
    InstrumentSerializer,
    L2OrderBookSerializer,
    LimitOrderBodySerializer,
    LimitOrderSerializer,
    MarketOrderBodySerializer,
    MarketOrderSerializer,
    NewUserSerializer,
    OkSerializer,
    TransactionSerializer,
    UserSerializer,
    WithdrawSerializer,
)

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _remaining(order: dict) -> Decimal:
    return Decimal(order["body"]["qty"]) - Decimal(order["filled"])


def http_validation_error(msg, loc=None):
    if loc is None:
        loc = ["body"]
    return Response(
        {"detail": [{"loc": loc, "msg": msg, "type": "validation_error"}]},
        status=422,
    )


# --------------------------------------------------------------------------- #
# in-memory state (только для демонстрационных целей)
# --------------------------------------------------------------------------- #

ORDERS = {}
ORDER_BOOK = defaultdict(lambda: {"BUY": [], "SELL": []})
TRADES = []

# balances: {user_id: {ticker: Decimal}}
BALANCES = defaultdict(lambda: defaultdict(Decimal))

INSTRUMENTS = {
    "MEMCOIN": {"name": "Memecoin", "ticker": "MEMCOIN"},
    "DODGE": {"name": "Dodge", "ticker": "DODGE"},
    "RUB": {"name": "Ruble", "ticker": "RUB"},
}

User = get_user_model()

# --------------------------------------------------------------------------- #
# order-matching engine
# --------------------------------------------------------------------------- #

def _apply_trade(
    buyer_id: str,
    seller_id: str,
    ticker: str,
    qty: Decimal,
    price: Decimal,
):
    total = qty * price
    BALANCES[buyer_id]["RUB"] -= total
    BALANCES[seller_id]["RUB"] += total
    BALANCES[buyer_id][ticker] += qty
    BALANCES[seller_id][ticker] -= qty


def execute_matches(order, counter_orders):
    ticker = order["body"]["ticker"]

    i = 0
    while _remaining(order) > 0 and i < len(counter_orders):
        counter = counter_orders[i]
        trade_qty = min(_remaining(order), _remaining(counter))
        if trade_qty <= 0:
            i += 1
            continue

        trade_price = Decimal(counter["body"]["price"])

        if order["order_type"] == "buy":
            buyer_id, seller_id = order["user_id"], counter["user_id"]
        else:
            buyer_id, seller_id = counter["user_id"], order["user_id"]

        _apply_trade(buyer_id, seller_id, ticker, trade_qty, trade_price)

        order["filled"] += float(trade_qty)
        counter["filled"] += float(trade_qty)

        TRADES.append(
            {
                "id": str(uuid.uuid4()),
                "timestamp": utcnow(),
                "ticker": ticker,
                "qty": float(trade_qty),
                "price": float(trade_price),
                "direction": order["order_type"].upper(),
                "order_id": order["id"],
                "user_id": buyer_id,
            }
        )

        if _remaining(counter) == 0:
            counter["status"] = "EXECUTED"
            counter_orders.pop(i)
        else:
            counter["status"] = "PARTIALLY_EXECUTED"
            i += 1

    if _remaining(order) == 0:
        order["status"] = "EXECUTED"
    elif order["filled"] > 0:
        order["status"] = "PARTIALLY_EXECUTED"


def match_market_order(order):
    direction = order["order_type"]
    ticker = order["body"]["ticker"]

    book_side = "SELL" if direction == "buy" else "BUY"
    counter_orders = ORDER_BOOK[ticker][book_side]
    counter_orders.sort(
        key=lambda o: o["body"]["price"],
        reverse=(direction == "sell"),
    )
    execute_matches(order, counter_orders)


def match_limit_order(order):
    direction = order["order_type"]
    ticker = order["body"]["ticker"]
    price = Decimal(order["body"]["price"])

    book_side = "SELL" if direction == "buy" else "BUY"
    counter_orders = [
        o
        for o in ORDER_BOOK[ticker][book_side]
        if (
            Decimal(o["body"]["price"]) <= price
            if direction == "buy"
            else Decimal(o["body"]["price"]) >= price
        )
    ]
    counter_orders.sort(
        key=lambda o: o["body"]["price"],
        reverse=(direction == "sell"),
    )

    execute_matches(order, counter_orders)

    if _remaining(order) > 0:  # still open → кладём в книгу
        ORDER_BOOK[ticker][direction.upper()].append(order)
        ORDER_BOOK[ticker][direction.upper()].sort(
            key=lambda o: o["body"]["price"], reverse=(direction == "buy")
        )


def process_order(order):
    if "price" in order["body"]:
        match_limit_order(order)
    else:
        match_market_order(order)


# --------------------------------------------------------------------------- #
# API views
# --------------------------------------------------------------------------- #

class RegisterView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(
        request_body=NewUserSerializer, responses={200: UserSerializer}
    )
    def post(self, request):
        serializer = NewUserSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=422)

        username = serializer.validated_data["name"]
        role = serializer.validated_data.get("role", User.Roles.USER)
        is_staff = role == User.Roles.ADMIN

        user = User.objects.create_user(username=username, role=role, is_staff=is_staff)

        # стартовый бонус
        BALANCES[str(user.id)]["RUB"] = Decimal("250")
        Account.objects.get_or_create(user=user, defaults={"balance": 250})

        data = {
            "id": str(user.id),
            "name": user.username,
            "role": user.role,
            "api_key": user.api_key,
        }
        return Response(data, status=200)


class InstrumentListView(APIView):
    def get(self, request):
        serializer = InstrumentSerializer(INSTRUMENTS.values(), many=True)
        return Response(serializer.data, status=200)


class L2OrderBookView(APIView):
    def get(self, request, ticker):
        ticker = ticker.upper()
        try:
            limit = int(request.GET.get("limit", 10))
            if not 1 <= limit <= 25:
                raise ValueError
        except ValueError:
            return http_validation_error("Invalid 'limit' parameter", ["query", "limit"])

        book = ORDER_BOOK[ticker]
        bids = sorted(
            book["BUY"], key=lambda o: o["body"]["price"], reverse=True
        )[:limit]
        asks = sorted(book["SELL"], key=lambda o: o["body"]["price"])[:limit]

        orderbook = {
            "bid_levels": [
                {"price": o["body"]["price"], "qty": _remaining(o)} for o in bids
            ],
            "ask_levels": [
                {"price": o["body"]["price"], "qty": _remaining(o)} for o in asks
            ],
        }
        serializer = L2OrderBookSerializer(orderbook)
        return Response(serializer.data, status=200)


class TransactionHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, ticker):
        ticker = ticker.upper()
        try:
            limit = int(request.GET.get("limit", 10))
            if not 1 <= limit <= 100:
                raise ValueError
        except ValueError:
            return http_validation_error("Invalid 'limit' parameter", ["query", "limit"])

        txs = [t for t in TRADES if t["ticker"] == ticker][:limit]
        serializer = TransactionSerializer(txs, many=True)
        return Response(serializer.data, status=200)


class BalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_id = str(request.user.id)
        balances = {
            ticker: float(amount) for ticker, amount in BALANCES[user_id].items()
        }
        for ticker in INSTRUMENTS:
            balances.setdefault(ticker, 0.0)
        return Response(balances, status=200)


class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get(self, request):
        user_id = str(request.user.id)
        orders = [o for o in ORDERS.values() if o["user_id"] == user_id]
        serializer = LimitOrderSerializer(orders, many=True)
        return Response(serializer.data, status=200)

    @swagger_auto_schema(
        request_body=LimitOrderBodySerializer, responses={200: CreateOrderResponseSerializer}
    )
    def post(self, request):
        body = request.data
        serializer = (
            LimitOrderBodySerializer(data=body)
            if "price" in body
            else MarketOrderBodySerializer(data=body)
        )
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)

        body_data = dict(serializer.validated_data)
        body_data["ticker"] = body_data["ticker"].upper()

        user_id = str(request.user.id)

        qty = Decimal(body_data["qty"])
        if body_data["direction"] == "BUY":
            price = Decimal(body_data.get("price") or 0)
            required = qty * price
            if BALANCES[user_id]["RUB"] < required:
                return http_validation_error("Insufficient funds")
        else:  # SELL
            if BALANCES[user_id][body_data["ticker"]] < qty:
                return http_validation_error("Insufficient asset qty")

        order_id = str(uuid.uuid4())
        order = {
            "id": order_id,
            "status": "NEW",
            "user_id": user_id,
            "timestamp": utcnow(),
            "order_type": body_data["direction"].lower(),
            "body": body_data,
            "filled": 0.0,
        }
        ORDERS[order_id] = order

        process_order(order)

        resp = {"success": True, "order_id": order_id}
        return Response(resp, status=200)


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
        direction = order["order_type"].upper()
        if order in ORDER_BOOK[ticker][direction]:
            ORDER_BOOK[ticker][direction].remove(order)
        return Response({"success": True}, status=200)


class AdminUserDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=404)
        user.delete()
        return Response({"success": True}, status=200)


class AdminInstrumentCreateView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(request_body=InstrumentSerializer, responses={200: OkSerializer})
    def post(self, request):
        serializer = InstrumentSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        data = serializer.validated_data
        ticker = data["ticker"].upper()
        if ticker in INSTRUMENTS:
            return http_validation_error("Instrument already exists", ["body", "ticker"])
        INSTRUMENTS[ticker] = {"name": data["name"], "ticker": ticker}
        ORDER_BOOK[ticker]  # ensure book created
        return Response({"success": True}, status=200)


class AdminInstrumentDeleteView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, ticker):
        ticker = ticker.upper()
        if ticker not in INSTRUMENTS:
            return Response(status=404)
        del INSTRUMENTS[ticker]
        ORDER_BOOK.pop(ticker, None)
        return Response({"success": True}, status=200)


class AdminBalanceDepositView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(request_body=DepositSerializer, responses={200: OkSerializer})
    def post(self, request):
        serializer = DepositSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        user_id = serializer.validated_data["user_id"]
        ticker = serializer.validated_data["ticker"].upper()
        amount = Decimal(serializer.validated_data["amount"])
        BALANCES[user_id][ticker] += amount
        return Response({"success": True}, status=200)


class AdminBalanceWithdrawView(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    @swagger_auto_schema(request_body=WithdrawSerializer, responses={200: OkSerializer})
    def post(self, request):
        serializer = WithdrawSerializer(data=request.data)
        if not serializer.is_valid():
            return http_validation_error(serializer.errors)
        user_id = serializer.validated_data["user_id"]
        ticker = serializer.validated_data["ticker"].upper()
        amount = Decimal(serializer.validated_data["amount"])
        if BALANCES[user_id][ticker] < amount:
            return http_validation_error("Insufficient balance", ["body", "amount"])
        BALANCES[user_id][ticker] -= amount
        return Response({"success": True}, status=status.HTTP_200_OK)
