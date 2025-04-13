from django.urls import path
from .views import WelcomeView, CreateOrderView, RegisterView, LoginView

urlpatterns = [
    path('', WelcomeView.as_view(), name='welcome'),
    path('trading/orders/', CreateOrderView.as_view(), name='create_order'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
]
