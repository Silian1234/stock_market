from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from drf_yasg.utils import swagger_auto_schema
from rest_framework.viewsets import ModelViewSet
from .services import process_order

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

    @swagger_auto_schema(
        request_body=OrderCreateSerializer,
        responses={201: OrderSerializer},
        operation_description="Создание заявки на покупку или продажу (лимитной или рыночной)"
    )
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


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @swagger_auto_schema(
        request_body=OrderSerializer,
        operation_description="Создать заявку (лимитную или рыночную) на покупку или продажу акций",
        responses={201: OrderSerializer}
    )
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return response

    def perform_create(self, serializer):
        order = serializer.save(remaining_quantity=serializer.validated_data['quantity'])
        process_order(order)

class MyOrdersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить список всех заявок текущего пользователя",
        responses={200: OrderSerializer(many=True)}
    )
    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class InstantBuyView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        request_body=OrderCreateSerializer,
        responses={201: OrderSerializer},
        operation_description="Мгновенная покупка акций по рыночной цене"
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            stock_id = data.get('stock_id')
            quantity = data.get('quantity')

            try:
                stock = Stock.objects.get(id=stock_id)
            except Stock.DoesNotExist:
                return Response({"detail": "Stock not found."}, status=status.HTTP_404_NOT_FOUND)

            try:
                account = Account.objects.get(user=request.user, currency="USD")
            except Account.DoesNotExist:
                return Response({"detail": "Account not found."}, status=status.HTTP_400_BAD_REQUEST)

            estimated_cost = stock.initial_price * quantity
            if account.balance < estimated_cost:
                return Response({"detail": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

            order = Order.objects.create(
                user=request.user,
                stock=stock,
                order_type="buy",
                order_mode="market",
                price=None,
                quantity=quantity,
                remaining_quantity=quantity
            )

            matching_engine.match_orders(order)

            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)