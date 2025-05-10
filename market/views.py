from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import FormParser
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Stock, Order, Trade, Holding
from .serializers import *
from .services.matching import execute_order
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class RegisterView(APIView):
    parser_classes = [FormParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
        ],
        operation_description="Регистрация нового пользователя",
        consumes=["application/x-www-form-urlencoded"],
        responses={201: openapi.Response("Пользователь зарегистрирован")}
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email', '')

        if not username or not password:
            return Response({"error": "Username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        if get_user_model().objects.filter(username=username).exists():
            return Response({"error": "Username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_user_model().objects.create_user(username=username, password=password, email=email)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    parser_classes = [FormParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
            openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True),
        ],
        operation_description="Вход пользователя и получение токена",
        consumes=["application/x-www-form-urlencoded"],
        responses={200: openapi.Response("Токен выдан")}
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key})
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class CreateOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [FormParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('stock_id', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('order_type', openapi.IN_FORM, type=openapi.TYPE_STRING, enum=['buy', 'sell'], required=True),
            openapi.Parameter('order_mode', openapi.IN_FORM, type=openapi.TYPE_STRING, enum=['limit', 'market'], required=True),
            openapi.Parameter('quantity', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=True),
            openapi.Parameter('price', openapi.IN_FORM, type=openapi.TYPE_NUMBER, required=False),
        ],
        consumes=['application/x-www-form-urlencoded'],
        responses={201: OrderSerializer},
        operation_description="Создание новой заявки (limit/market) на покупку или продажу"
    )
    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            stock = Stock.objects.get(id=data['stock_id'])

            order = Order.objects.create(
                user=request.user,
                stock=stock,
                order_type=data['order_type'],
                order_mode=data['order_mode'],
                price=data['price'],
                quantity=data['quantity'],
                remaining_quantity=data['quantity']
            )

            execute_order(order)
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CancelOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('order_id', openapi.IN_PATH, description="ID заявки", type=openapi.TYPE_INTEGER)
        ],
        operation_description="Отмена активной (неисполненной) заявки"
    )
    def delete(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user, is_filled=False)
            order.delete()
            return Response({"status": "order cancelled"}, status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            return Response({"error": "not found or already filled"}, status=status.HTTP_404_NOT_FOUND)


class MyOrdersView(ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = OrderSerializer

    @swagger_auto_schema(operation_description="Получить список заявок пользователя")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class HoldingsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(operation_description="Получить список всех активов пользователя")
    def get(self, request):
        holdings = Holding.objects.filter(user=request.user)
        return Response(HoldingSerializer(holdings, many=True).data)


class TradeHistoryView(ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TradeSerializer

    @swagger_auto_schema(operation_description="История совершённых сделок пользователя")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Trade.objects.filter(buyer=self.request.user) | Trade.objects.filter(seller=self.request.user)


class OrderBookView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('stock_id', openapi.IN_PATH, description="ID акции", type=openapi.TYPE_INTEGER)
        ],
        operation_description="Получить стакан заявок (buy/sell) по акции"
    )
    def get(self, request, stock_id):
        buy_orders = Order.objects.filter(stock_id=stock_id, order_type='buy', is_filled=False).order_by('-price', 'created_at')
        sell_orders = Order.objects.filter(stock_id=stock_id, order_type='sell', is_filled=False).order_by('price', 'created_at')

        return Response({
            'buy_orders': OrderSerializer(buy_orders, many=True).data,
            'sell_orders': OrderSerializer(sell_orders, many=True).data,
        })

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить профиль текущего пользователя",
        responses={200: UserSerializer},
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class StockListView(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Получить список всех доступных акций",
        responses={200: StockSerializer(many=True)}
    )
    def get(self, request):
        stocks = Stock.objects.all()
        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data)
