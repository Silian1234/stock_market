from django.urls import path
from .views import *

urlpatterns = [
    path("v1/register/", RegisterView.as_view()),
    path("v1/instruments/", InstrumentListView.as_view()),
    path("v1/instruments/<str:ticker>/orderbook/", OrderBookView.as_view()),
    path("v1/instruments/<str:ticker>/history/", TradeHistoryView.as_view()),
    path("v1/balance/", BalanceView.as_view()),
    path("v1/orders/", OrderListView.as_view()),
    path("v1/orders/place/", OrderCreateView.as_view()),
    path("v1/orders/<int:order_id>/", OrderDetailView.as_view()),
    path("v1/orders/<int:order_id>/cancel/", OrderCancelView.as_view()),
    path("v1/admin/instruments/", AdminCreateInstrumentView.as_view()),
    path("v1/admin/instruments/<str:ticker>/", AdminDeleteInstrumentView.as_view()),
    path('v1/public/register', RegisterView.as_view()),
    path('v1/admin/balance/deposit', AdminDepositView.as_view()),
    path('v1/admin/balance/withdraw', AdminWithdrawView.as_view()),
]
