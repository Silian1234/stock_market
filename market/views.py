from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import Stock, Order, Trade, Account
from .serializers import *
from .matching import match_orders

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "success": True,
                "api_key": user.api_key,
                "user_id": str(user.id)
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class InstrumentListView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)


class OrderBookView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, ticker):
        stock = get_object_or_404(Stock, symbol=ticker)
        buy_orders = Order.objects.filter(stock=stock, order_type='buy', is_filled=False).order_by('-price')[:10]
        sell_orders = Order.objects.filter(stock=stock, order_type='sell', is_filled=False).order_by('price')[:10]
        return Response({
            'buy': OrderSerializer(buy_orders, many=True).data,
            'sell': OrderSerializer(sell_orders, many=True).data
        })


class TradeHistoryView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, ticker):
        stock = get_object_or_404(Stock, symbol=ticker)
        trades = Trade.objects.filter(stock=stock).order_by('-created_at')[:50]
        return Response(TradeSerializer(trades, many=True).data)


class BalanceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        account = get_object_or_404(Account, user=request.user)
        return Response(AccountSerializer(account).data)


class OrderCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            stock = get_object_or_404(Stock, id=serializer.validated_data['stock_id'])
            order = Order.objects.create(
                user=request.user,
                stock=stock,
                order_type=serializer.validated_data['order_type'],
                order_mode=serializer.validated_data['order_mode'],
                price=serializer.validated_data.get('price'),
                quantity=serializer.validated_data['quantity'],
                remaining_quantity=serializer.validated_data['quantity']
            )
            match_orders(order)
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        return Response(OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        return Response(OrderSerializer(order).data)


class OrderCancelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)
        if order.is_filled:
            return Response({'detail': 'Order already filled'}, status=status.HTTP_400_BAD_REQUEST)
        order.is_filled = True
        order.remaining_quantity = 0
        order.save()
        return Response({'detail': 'Order cancelled successfully'})


class AdminCreateInstrumentView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        serializer = StockCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminDeleteInstrumentView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def delete(self, request, ticker):
        stock = get_object_or_404(Stock, symbol=ticker)
        stock.delete()
        return Response({'detail': 'Instrument deleted'})

class AdminDepositView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        amount = float(request.data.get("amount", 0))
        user = get_object_or_404(User, id=user_id)
        account, _ = Account.objects.get_or_create(user=user)
        account.balance += amount
        account.save()
        return Response({"success": True, "balance": account.balance})


class AdminWithdrawView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        user_id = request.data.get("user_id")
        amount = float(request.data.get("amount", 0))
        user = get_object_or_404(User, id=user_id)
        account = get_object_or_404(Account, user=user)
        if account.balance < amount:
            return Response({"success": False, "message": "Insufficient funds"}, status=400)
        account.balance -= amount
        account.save()
        return Response({"success": True, "balance": account.balance})