from django.urls import path
from .views import WelcomeView, CreateOrderView
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),
    path('trading/orders/', CreateOrderView.as_view(), name='create_order'),
    path('auth/token/', obtain_auth_token, name='obtain_auth_token'),
]
