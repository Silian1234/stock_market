from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from .serializers import (
    OrderCreateSerializer, OrderSerializer,
    UserRegistrationSerializer, LoginSerializer
)
from .models import Stock, Account, Order
from core.matching import MatchingEngine

matching_engine = MatchingEngine()

class WelcomeView(APIView):
    def get(self, request):
        return Response({"message": "Welcome to the Stock Market API!"})

class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            stock_id = data.get('stock_id')
            quantity = data.get('quantity')
            side = data.get('side')
            order_type = data.get('order_type')
            price = data.get('price')
            try:
                stock = Stock.objects.get(id=stock_id)
            except Stock.DoesNotExist:
                return Response({"detail": "Stock not found."}, status=status.HTTP_404_NOT_FOUND)
            try:
                account = Account.objects.get(user=request.user, currency="USD")
            except Account.DoesNotExist:
                return Response({"detail": "Account not found. Create a USD account first."}, status=status.HTTP_400_BAD_REQUEST)
            if order_type == "MARKET" and side == "BUY":
                estimated_cost = stock.initial_price * quantity
                if account.balance < estimated_cost:
                    return Response({"detail": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)
            order_price = price if order_type == "LIMIT" else stock.initial_price
            order = Order.objects.create(
                user=request.user,
                stock=stock,
                order_type=order_type,
                side=side,
                price=order_price,
                quantity=quantity
            )
            matching_engine.match_orders(order)
            order_serializer = OrderSerializer(order)
            return Response(order_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    @swagger_auto_schema(request_body=UserRegistrationSerializer)
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    @swagger_auto_schema(request_body=LoginSerializer)
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
