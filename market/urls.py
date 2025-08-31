from django.urls import path
from .views import (
    RegisterView, InstrumentListView, L2OrderBookView, TransactionHistoryView,
    BalanceView, OrderListCreateView, OrderDetailView,
    AdminUserDeleteView, AdminInstrumentCreateView, AdminInstrumentDeleteView,
    AdminBalanceDepositView, AdminBalanceWithdrawView
)

urlpatterns = [
    path('public/register', RegisterView.as_view(), name='register'),
    path('public/instrument', InstrumentListView.as_view(), name='instruments'),
    path('public/orderbook/<str:ticker>', L2OrderBookView.as_view(), name='orderbook'),
    path('public/transactions/<str:ticker>', TransactionHistoryView.as_view(), name='transactions'),
    path('balance', BalanceView.as_view(), name='balance'),
    path('order', OrderListCreateView.as_view(), name='order'),
    path('order/<uuid:order_id>', OrderDetailView.as_view(), name='order-detail'),
    path('admin/user/<uuid:user_id>', AdminUserDeleteView.as_view(), name='admin-user-delete'),
    path('admin/instrument', AdminInstrumentCreateView.as_view(), name='admin-instrument-create'),
    path('admin/instrument/<str:ticker>', AdminInstrumentDeleteView.as_view(), name='admin-instrument-delete'),
    path('admin/balance/deposit', AdminBalanceDepositView.as_view(), name='admin-balance-deposit'),
    path('admin/balance/withdraw', AdminBalanceWithdrawView.as_view(), name='admin-balance-withdraw'),
]
