from django.urls import path
from .views import (
    RegisterView, LoginView,
    CreateOrderView, CancelOrderView, MyOrdersView,
    HoldingsView, TradeHistoryView, OrderBookView,
    UserProfileView, StockListView
)

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/profile/', UserProfileView.as_view(), name='profile'),
    path('orders/create/', CreateOrderView.as_view(), name='create_order'),
    path('orders/cancel/<int:order_id>/', CancelOrderView.as_view(), name='cancel_order'),
    path('orders/my/', MyOrdersView.as_view({'get': 'list'}), name='my_orders'),
    path('holdings/', HoldingsView.as_view(), name='holdings'),
    path('trades/history/', TradeHistoryView.as_view({'get': 'list'}), name='trade_history'),
    path('orderbook/<int:stock_id>/', OrderBookView.as_view(), name='order_book'),
    path('stocks/all/', StockListView.as_view(), name='stock_list'),
]
